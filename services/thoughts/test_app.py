import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from app import create_app, digest
from passwords import hash_password, validate_hash, verify_password

PASSWORD = "test-only-strong-password-1234"


@pytest.fixture(scope="session")
def encoded():
    return hash_password(PASSWORD)


def config(path, encoded=""):
    return {"THOUGHTS_DB": str(path), "THOUGHTS_FRONTEND_URL": "http://localhost:8769/thoughts/",
            "THOUGHTS_PASSWORD_HASH": encoded}


@pytest.fixture
def service(tmp_path, encoded):
    path = tmp_path / 'test.sqlite3'
    app = create_app(config(path, encoded))
    with sqlite3.connect(path) as con:
        con.execute('INSERT INTO auth(key,kind,expires,verifier) VALUES(?,?,?,?)',
                    (digest('owner-token'), 'password-session', int(time.time()) + 600, digest(encoded)))
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


def test_password_login_and_session_storage(service):
    client, path = service
    assert client.post('/auth/login', json={'password': 'wrong'}).status_code == 401
    response = client.post('/auth/login', json={'password': PASSWORD})
    assert response.status_code == 200
    token = response.json()['token']
    assert len(token) >= 64
    auth = {'Authorization': 'Bearer ' + token}
    assert client.get('/auth/me', headers=auth).json() == {'login': 'Bamb0oChen', 'role': 'owner'}
    assert client.post('/posts', headers=auth, json={'body': 'draft'}).status_code == 201
    with sqlite3.connect(path) as con:
        row = con.execute("SELECT * FROM auth WHERE key=?", (digest(token),)).fetchone()
        assert row and row[1] == 'password-session'
        assert PASSWORD not in str(row) and token not in str(row)
        assert 43190 <= row[2] - time.time() <= 43200
    assert client.post('/auth/logout', headers=auth).status_code == 204
    assert client.get('/admin/posts', headers=auth).status_code == 401


def test_expired_and_legacy_sessions_are_rejected(service):
    client, path = service
    with sqlite3.connect(path) as con:
        con.execute("UPDATE auth SET expires=0")
        con.execute("INSERT INTO auth(key,kind,expires) VALUES(?,?,?)",
                    (digest('legacy-oauth'), 'session', int(time.time()) + 600))
    assert client.get('/auth/me', headers=AUTH).status_code == 401
    assert client.get('/admin/posts', headers={'Authorization': 'Bearer legacy-oauth'}).status_code == 401
    assert client.get('/auth/start').status_code == 404
    assert client.get('/auth/callback').status_code == 404
    assert client.post('/auth/exchange', json={}).status_code == 404


def test_password_rotation_and_posts_survive_restart(service, encoded):
    client, path = service
    post = client.post('/posts', headers=AUTH, json={'body': 'keep this', 'status': 'published'}).json()
    with TestClient(create_app(config(path, encoded))) as restarted:
        assert restarted.get('/auth/me', headers=AUTH).status_code == 200
        assert restarted.get('/posts').json()['items'][0]['id'] == post['id']
    replacement = hash_password(PASSWORD + '-changed')
    with TestClient(create_app(config(path, replacement))) as changed:
        assert changed.get('/auth/me', headers=AUTH).status_code == 401
        assert changed.get('/posts').json()['items'][0]['body'] == 'keep this'
        assert changed.post('/auth/login', json={'password': PASSWORD}).status_code == 401
        assert changed.post('/auth/login', json={'password': PASSWORD + '-changed'}).status_code == 200
    with TestClient(create_app(config(path))) as disabled:
        assert disabled.get('/auth/me', headers=AUTH).status_code == 401


def test_missing_config_is_read_only(tmp_path):
    with TestClient(create_app(config(tmp_path / 'disabled.sqlite3'))) as client:
        assert client.get('/health').json()['login_configured'] is False
        assert client.get('/posts').status_code == 200
        assert client.post('/auth/login', json={'password': PASSWORD}).status_code == 503


def test_hash_validation_and_salt(encoded):
    assert verify_password(PASSWORD, encoded)
    assert not verify_password(PASSWORD + 'x', encoded)
    assert hash_password(PASSWORD) != encoded
    assert len(validate_hash(encoded)[0]) == 16
    for invalid in ('plaintext-password', 'scrypt-v1$bad$bad', encoded + 'x'):
        with pytest.raises(ValueError):
            validate_hash(invalid)
    with pytest.raises(ValueError):
        hash_password('short')


def test_invalid_config_fails_closed(tmp_path):
    cfg = config(tmp_path / 'bad.sqlite3', 'plaintext-password')
    with pytest.raises(ValueError):
        create_app(cfg)
    cfg = config(tmp_path / 'bad.sqlite3')
    cfg['THOUGHTS_FRONTEND_URL'] = 'http://public.example/thoughts/'
    with pytest.raises(ValueError):
        create_app(cfg)


@pytest.mark.parametrize('payload', [{}, {'password': 123}, {'password': 'x' * 257}, {'password': ''}])
def test_invalid_login_never_echoes_password(service, payload):
    client, _ = service
    response = client.post('/auth/login', json=payload)
    assert response.status_code == 422
    assert response.json() == {'detail': '输入格式不正确或内容过长'}


def test_login_throttling_persists_and_expires(service, encoded, monkeypatch):
    client, path = service
    monkeypatch.setattr('app.verify_password', lambda *args: False)
    for _ in range(5):
        assert client.post('/auth/login', json={'password': 'wrong'}).status_code == 401
    response = client.post('/auth/login', json={'password': PASSWORD})
    assert response.status_code == 429 and response.headers['retry-after'] == '900'
    with TestClient(create_app(config(path, encoded))) as restarted:
        assert restarted.post('/auth/login', json={'password': 'wrong'}).status_code == 429
    with sqlite3.connect(path) as con:
        con.execute('UPDATE login_attempts SET attempted_at=?', (time.time() - 901,))
    assert client.post('/auth/login', json={'password': 'wrong'}).status_code == 401


def test_global_login_throttle(service):
    client, path = service
    with sqlite3.connect(path) as con:
        con.executemany('INSERT INTO login_attempts VALUES(?,?)',
                        [(digest(str(i)), time.time()) for i in range(30)])
    assert client.post('/auth/login', json={'password': PASSWORD}).status_code == 429
    assert client.get('/posts').status_code == 200


def test_security_headers(service):
    client, _ = service
    response = client.post('/auth/login', json={'password': 'wrong'})
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_cors(service):
    client, _ = service
    headers = {'Origin': 'http://localhost:8769', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'authorization,content-type'}
    assert client.options('/posts', headers=headers).headers['access-control-allow-origin'] == 'http://localhost:8769'
    headers['Origin'] = 'https://attacker.example'
    assert 'access-control-allow-origin' not in client.options('/posts', headers=headers).headers
