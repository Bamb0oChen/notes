"""Single-author notes API. Secrets and GitHub access tokens never reach the site."""
import base64
import hashlib
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def challenge(value):
    return base64.urlsafe_b64encode(hashlib.sha256(value.encode()).digest()).decode().rstrip('=')


class PostInput(BaseModel):
    title: str = Field(default='', max_length=120)
    body: str = Field(min_length=1, max_length=20000)
    status: Literal['draft', 'published'] = 'draft'
    version: int | None = Field(default=None, ge=1)

    @field_validator('body')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('正文不能为空')
        return value.strip()


class Exchange(BaseModel):
    code: str = Field(min_length=32, max_length=128)
    verifier: str = Field(min_length=43, max_length=128)


def create_app(config=None):
    cfg = dict(os.environ) if config is None else config
    database = Path(cfg.get('THOUGHTS_DB', 'data/thoughts.sqlite3'))
    frontend = cfg.get('THOUGHTS_FRONTEND_URL', 'http://localhost:8769/随想/')
    parsed = urlsplit(frontend)
    origin = f'{parsed.scheme}://{parsed.netloc}'
    callback = cfg.get('THOUGHTS_CALLBACK_URL', 'http://localhost:8770/auth/callback')
    for address in (frontend, callback):
        target = urlsplit(address)
        if target.scheme not in ('http', 'https') or not target.hostname or target.fragment or target.query:
            raise ValueError('前端和 OAuth 回调必须是无 query/fragment 的完整 HTTP(S) URL')
        if target.scheme == 'http' and target.hostname not in ('localhost', '127.0.0.1'):
            raise ValueError('非本地地址必须使用 HTTPS')
    owner_id = int(cfg.get('THOUGHTS_OWNER_ID', '247085583'))
    database.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def db():
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with db() as con:
        con.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('draft','published')),
            created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            published_at INTEGER, version INTEGER NOT NULL DEFAULT 1
          );
          CREATE TABLE IF NOT EXISTS auth (
            key TEXT PRIMARY KEY, kind TEXT NOT NULL, expires INTEGER NOT NULL,
            verifier TEXT NOT NULL DEFAULT '', browser_challenge TEXT NOT NULL DEFAULT ''
          );
          CREATE INDEX IF NOT EXISTS posts_public ON posts(status,published_at);
        ''')

    app = FastAPI(title='Notes · 随想', docs_url=None, redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=[origin],
                       allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
                       allow_headers=['Authorization', 'Content-Type'])

    @app.middleware('http')
    async def protect(request: Request, call_next):
        from fastapi.responses import JSONResponse
        # Bound JSON parsing memory as well as the reverse proxy's upload limit.
        if request.method in ('POST', 'PUT'):
            parts, size = [], 0
            async for part in request.stream():
                size += len(part)
                if size > 128000:
                    return JSONResponse({'detail': '内容过长'}, status_code=413)
                parts.append(part)
            request._body = b''.join(parts)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    def consume(key, kind):
        with db() as con:
            row = con.execute('DELETE FROM auth WHERE key=? AND kind=? RETURNING *',
                              (digest(key), kind)).fetchone()
        if not row or row['expires'] <= time.time():
            raise HTTPException(401, '登录链接已失效，请重新登录')
        return row

    def put_auth(key, kind, expires, verifier='', browser_challenge=''):
        with db() as con:
            con.execute('DELETE FROM auth WHERE expires<=?', (int(time.time()),))
            if con.execute('SELECT count(*) FROM auth').fetchone()[0] >= 1000:
                raise HTTPException(429, '登录请求过多，请稍后再试')
            con.execute('INSERT INTO auth VALUES(?,?,?,?,?)',
                        (digest(key), kind, expires, verifier, browser_challenge))

    def owner(authorization: str = Header(default='')):
        token = authorization.removeprefix('Bearer ')
        with db() as con:
            row = con.execute("SELECT expires FROM auth WHERE key=? AND kind='session'",
                              (digest(token),)).fetchone()
        if not authorization.startswith('Bearer ') or not row or row['expires'] <= time.time():
            raise HTTPException(401, '请使用作者账号登录')
        return token

    @app.get('/health')
    def health():
        return {'ok': True, 'login_configured': bool(cfg.get('GITHUB_CLIENT_ID') and cfg.get('GITHUB_CLIENT_SECRET'))}

    @app.get('/auth/start')
    def start(browser_challenge: str = Query(pattern=r'^[A-Za-z0-9_-]{43}$')):
        if not cfg.get('GITHUB_CLIENT_ID') or not cfg.get('GITHUB_CLIENT_SECRET'):
            raise HTTPException(503, '作者登录尚未配置')
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        put_auth(state, 'oauth', int(time.time()) + 600, verifier, browser_challenge)
        return RedirectResponse('https://github.com/login/oauth/authorize?' + urlencode({
            'client_id': cfg['GITHUB_CLIENT_ID'], 'redirect_uri': callback,
            'scope': '', 'state': state, 'code_challenge': challenge(verifier),
            'code_challenge_method': 'S256', 'allow_signup': 'false', 'login': 'Bamb0oChen',
        }), status_code=303)

    @app.get('/auth/callback')
    async def oauth_callback(state: str = Query(max_length=128), code: str = Query(default='', max_length=512), error: str = ''):
        row = consume(state, 'oauth')
        if error or not code:
            return RedirectResponse(frontend + '#thoughts-error=cancelled', status_code=303)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                result = await client.post('https://github.com/login/oauth/access_token',
                    headers={'Accept': 'application/json'}, data={
                        'client_id': cfg['GITHUB_CLIENT_ID'], 'client_secret': cfg['GITHUB_CLIENT_SECRET'],
                        'code': code, 'redirect_uri': callback, 'code_verifier': row['verifier'],
                    })
                result.raise_for_status()
                github_token = result.json().get('access_token')
                if not github_token:
                    raise ValueError('OAuth exchange failed')
                result = await client.get('https://api.github.com/user', headers={
                    'Authorization': f'Bearer {github_token}', 'Accept': 'application/vnd.github+json',
                    'X-GitHub-Api-Version': '2022-11-28',
                })
                result.raise_for_status()
                account = result.json()
        except (httpx.HTTPError, ValueError):
            return RedirectResponse(frontend + '#thoughts-error=github', status_code=303)
        # Immutable identity, not a username supplied by the browser.
        if account.get('id') != owner_id:
            return RedirectResponse(frontend + '#thoughts-error=forbidden', status_code=303)
        handoff = secrets.token_urlsafe(32)
        put_auth(handoff, 'handoff', int(time.time()) + 60, browser_challenge=row['browser_challenge'])
        return RedirectResponse(frontend + '#thoughts-code=' + handoff, status_code=303)

    @app.post('/auth/exchange')
    def exchange(payload: Exchange):
        row = consume(payload.code, 'handoff')
        if not secrets.compare_digest(challenge(payload.verifier), row['browser_challenge']):
            raise HTTPException(401, '登录浏览器不匹配')
        token = secrets.token_urlsafe(48)
        put_auth(token, 'session', int(time.time()) + 12 * 3600)
        return {'token': token}

    @app.get('/auth/me')
    def me(token=Depends(owner)):
        return {'login': 'Bamb0oChen', 'id': owner_id}

    @app.post('/auth/logout', status_code=204)
    def logout(token=Depends(owner)):
        with db() as con:
            con.execute('DELETE FROM auth WHERE key=?', (digest(token),))

    def listing(public, before, limit):
        # Stable keyset cursor, avoiding duplicates when newer cards are published.
        where, args = ('status=\'published\'' if public else '1=1'), []
        order = 'published_at' if public else 'created_at'
        if before:
            with db() as con:
                previous = con.execute(f'SELECT {order} FROM posts WHERE id=? AND {where}', (before,)).fetchone()
            if previous:
                where += f' AND ({order} < ? OR ({order} = ? AND id < ?))'
                args.extend([previous[0], previous[0], before])
            else:
                raise HTTPException(409, '列表已更新，请刷新')
        with db() as con:
            rows = con.execute(f'SELECT * FROM posts WHERE {where} ORDER BY {order} DESC,id DESC LIMIT ?',
                               [*args, limit + 1]).fetchall()
        return {'items': [dict(r) for r in rows[:limit]],
                'next': rows[limit - 1]['id'] if len(rows) > limit else None}

    @app.get('/posts')
    def public_posts(before: str = '', limit: int = Query(default=20, ge=1, le=50)):
        return listing(True, before, limit)

    @app.get('/admin/posts')
    def own_posts(before: str = '', limit: int = Query(default=20, ge=1, le=50), token=Depends(owner)):
        return listing(False, before, limit)

    @app.post('/posts', status_code=201)
    def create(payload: PostInput, token=Depends(owner)):
        key, now = secrets.token_hex(16), int(time.time())
        with db() as con:
            con.execute('INSERT INTO posts VALUES(?,?,?,?,?,?,?,1)',
                        (key, payload.title.strip(), payload.body, payload.status, now, now,
                         now if payload.status == 'published' else None))
            return dict(con.execute('SELECT * FROM posts WHERE id=?', (key,)).fetchone())

    @app.put('/posts/{key}')
    def update(key: str, payload: PostInput, token=Depends(owner)):
        now = int(time.time())
        with db() as con:
            row = con.execute('UPDATE posts SET title=?,body=?,status=?,updated_at=?, '
                              "published_at=CASE WHEN ?='published' THEN COALESCE(published_at,?) ELSE NULL END, "
                              'version=version+1 WHERE id=? AND version=? RETURNING *',
                              (payload.title.strip(), payload.body, payload.status, now,
                               payload.status, now, key, payload.version)).fetchone()
        if not row:
            raise HTTPException(409, '内容已更新或删除，请刷新后重试；编辑框内容已保留')
        return dict(row)

    @app.delete('/posts/{key}', status_code=204)
    def delete(key: str, version: int = Query(ge=1), token=Depends(owner)):
        with db() as con:
            result = con.execute('DELETE FROM posts WHERE id=? AND version=?', (key, version))
        if not result.rowcount:
            raise HTTPException(409, '内容已更新或删除，请刷新后重试')

    return app


app = create_app()
