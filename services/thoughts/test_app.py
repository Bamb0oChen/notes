import sqlite3
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient

from app import challenge, create_app, digest


@pytest.fixture
def service(tmp_path):
    path = tmp_path / 'test.sqlite3'
    app = create_app({
        'THOUGHTS_DB': str(path), 'THOUGHTS_FRONTEND_URL': 'http://localhost:8769/thoughts/',
        'GITHUB_CLIENT_ID': 'test-client', 'GITHUB_CLIENT_SECRET': 'test-secret',
    })
    with sqlite3.connect(path) as con:
        con.execute('INSERT INTO auth(key,kind,expires) VALUES(?,?,?)',
                    (digest('owner-token'), 'session', int(time.time()) + 600))
    return TestClient(app), path


AUTH = {'Authorization': 'Bearer owner-token'}


def test_public_cannot_write_or_read_drafts(service):
    client, _ = service
    assert client.post('/posts', json={'body': 'forged'}).status_code == 401
    assert client.get('/admin/posts').status_code == 401
    assert client.get('/auth/me', headers={'Authorization': 'Bearer Bamb0oChen'}).status_code == 401
    draft = client.post('/posts', headers=AUTH, json={'body': 'private'}).json()
    assert client.get('/posts').json()['items'] == []
    assert client.get('/admin/posts', headers=AUTH).json()['items'][0]['id'] == draft['id']
    assert client.put('/posts/' + draft['id'], json={'body': 'attack', 'version': 1}).status_code == 401
    assert client.delete('/posts/' + draft['id'] + '?version=1').status_code == 401


def test_publish_edit_unpublish_conflicts_delete(service):
    client, _ = service
    post = client.post('/posts', headers=AUTH, json={'title': '第一条', 'body': '<script>alert(1)</script>\n正文', 'status': 'published'}).json()
    assert client.get('/posts').json()['items'][0]['id'] == post['id']
    path = '/posts/' + post['id']
    assert client.put(path, headers=AUTH, json={'body': 'draft now', 'version': 1}).status_code == 200
    assert client.get('/posts').json()['items'] == []
    assert client.put(path, headers=AUTH, json={'body': 'stale', 'version': 1}).status_code == 409
    assert client.delete(path + '?version=1', headers=AUTH).status_code == 409
    assert client.delete(path + '?version=2', headers=AUTH).status_code == 204
    assert client.get('/admin/posts', headers=AUTH).json()['items'] == []


def test_validation_and_limit(service):
    client, _ = service
    for payload in ({'body': '  '}, {'body': 'a' * 20001}, {'body': 'ok', 'status': 'invalid'}):
        assert client.post('/posts', headers=AUTH, json=payload).status_code == 422
    assert client.post('/posts', headers=AUTH, content='x' * 128001).status_code == 413
    assert client.get('/posts?limit=9999').status_code == 422


def test_keyset_and_logout(service):
    client, _ = service
    for i in range(4):
        client.post('/posts', headers=AUTH, json={'body': str(i), 'status': 'published'})
    first = client.get('/posts?limit=2').json()
    second = client.get('/posts?limit=2&before=' + first['next']).json()
    assert len({p['id'] for p in first['items'] + second['items']}) == 4
    assert second['next'] is None
    assert client.post('/auth/logout', headers=AUTH).status_code == 204
    assert client.get('/auth/me', headers=AUTH).status_code == 401


@pytest.mark.parametrize('account_id,allowed', [(247085583, True), (12345, False)])
def test_oauth_identity_state_pkce_and_replay(service, monkeypatch, account_id, allowed):
    client, _ = service
    verifier = 'browser-verifier-' + 'a' * 48
    start = client.get('/auth/start?browser_challenge=' + challenge(verifier), follow_redirects=False)
    params = parse_qs(urlsplit(start.headers['location']).query)
    assert params['code_challenge_method'] == ['S256']
    state = params['state'][0]

    class GitHub:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, data, **kwargs):
            assert challenge(data['code_verifier']) == params['code_challenge'][0]
            return httpx.Response(200, json={'access_token': 'secret-github-token'}, request=httpx.Request('POST', url))
        async def get(self, url, **kwargs):
            return httpx.Response(200, json={'id': account_id, 'login': 'Bamb0oChen'}, request=httpx.Request('GET', url))

    monkeypatch.setattr(httpx, 'AsyncClient', GitHub)
    assert client.get('/auth/callback?state=forged&code=test').status_code == 401
    callback = client.get('/auth/callback', params={'state': state, 'code': 'test'}, follow_redirects=False)
    assert client.get('/auth/callback', params={'state': state, 'code': 'test'}).status_code == 401
    fragment = parse_qs(urlsplit(callback.headers['location']).fragment)
    if not allowed:
        assert fragment == {'thoughts-error': ['forbidden']}
        return
    code = fragment['thoughts-code'][0]
    exchange = client.post('/auth/exchange', json={'code': code, 'verifier': verifier})
    assert exchange.status_code == 200
    assert 'secret-github-token' not in exchange.text
    token = exchange.json()['token']
    assert client.get('/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 200
    assert client.post('/auth/exchange', json={'code': code, 'verifier': verifier}).status_code == 401


def test_wrong_browser_and_expired_session(service):
    client, path = service
    with sqlite3.connect(path) as con:
        con.execute('INSERT INTO auth VALUES(?,?,?,?,?)', (digest('h' * 43), 'handoff', int(time.time()) + 60, '', challenge('a' * 43)))
        con.execute("UPDATE auth SET expires=0 WHERE kind='session'")
    assert client.post('/auth/exchange', json={'code': 'h' * 43, 'verifier': 'b' * 43}).status_code == 401
    assert client.get('/auth/me', headers=AUTH).status_code == 401


def test_cors(service):
    client, _ = service
    headers = {'Origin': 'http://localhost:8769', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'authorization,content-type'}
    assert client.options('/posts', headers=headers).headers['access-control-allow-origin'] == 'http://localhost:8769'
    headers['Origin'] = 'https://attacker.example'
    assert 'access-control-allow-origin' not in client.options('/posts', headers=headers).headers
