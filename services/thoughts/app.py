"""Single-author notes API with server-verified password sessions."""
import hashlib
import os
import secrets
import sqlite3
import time
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from passwords import validate_hash, verify_password
from pydantic import BaseModel, Field, field_validator


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


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


class LoginInput(BaseModel):
    password: str = Field(min_length=1, max_length=256)


def create_app(config=None):
    cfg = dict(os.environ) if config is None else config
    database = Path(cfg.get('THOUGHTS_DB', 'data/thoughts.sqlite3'))
    frontend = cfg.get('THOUGHTS_FRONTEND_URL', 'http://localhost:8769/随想/')
    parsed = urlsplit(frontend)
    origin = f'{parsed.scheme}://{parsed.netloc}'
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.fragment or parsed.query:
        raise ValueError('前端必须是无 query/fragment 的完整 HTTP(S) URL')
    if parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1'):
        raise ValueError('非本地地址必须使用 HTTPS')
    password_hash = cfg.get('THOUGHTS_PASSWORD_HASH', '')
    if password_hash:
        validate_hash(password_hash)
    credential = digest(password_hash)
    password_lock = threading.Lock()
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
          CREATE TABLE IF NOT EXISTS login_attempts (client TEXT NOT NULL, attempted_at REAL NOT NULL);
          CREATE INDEX IF NOT EXISTS login_attempts_time ON login_attempts(attempted_at);
          CREATE INDEX IF NOT EXISTS posts_public ON posts(status,published_at);
        ''')

    app = FastAPI(title='Notes · 随想', docs_url=None, redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=[origin],
                       allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
                       allow_headers=['Authorization', 'Content-Type'])

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError):
        # Pydantic's default response includes rejected input, which may contain a password.
        return JSONResponse({'detail': '输入格式不正确或内容过长'}, status_code=422)

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
            row = con.execute("SELECT expires FROM auth WHERE key=? AND kind='password-session' AND verifier=?",
                              (digest(token), credential)).fetchone()
        if not password_hash or not authorization.startswith('Bearer ') or not row or row['expires'] <= time.time():
            raise HTTPException(401, '请先输入管理密码解锁')
        return token

    @app.get('/health')
    def health():
        return {'ok': True, 'login_configured': bool(password_hash)}

    @app.post('/auth/login')
    def login(payload: LoginInput, request: Request):
        if not password_hash:
            raise HTTPException(503, '管理密码尚未配置')
        now = time.time()
        client = digest(request.client.host if request.client else 'unknown')
        # Persist the limits across process restarts; serialize admission across workers.
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('DELETE FROM login_attempts WHERE attempted_at<=?', (now - 900,))
            total = con.execute('SELECT count(*) FROM login_attempts').fetchone()[0]
            own = con.execute('SELECT count(*) FROM login_attempts WHERE client=?', (client,)).fetchone()[0]
            limited = total >= 30 or own >= 5
            if not limited:
                con.execute('INSERT INTO login_attempts VALUES(?,?)', (client, now))
        if limited:
            raise HTTPException(429, '尝试次数过多，请 15 分钟后再试', headers={'Retry-After': '900'})
        # scrypt intentionally uses memory; do not run many verifications concurrently.
        if not password_lock.acquire(blocking=False):
            raise HTTPException(429, '正在处理登录，请稍后再试', headers={'Retry-After': '5'})
        try:
            valid = verify_password(payload.password, password_hash)
        finally:
            password_lock.release()
        if not valid:
            raise HTTPException(401, '管理密码不正确')
        token = secrets.token_urlsafe(48)
        put_auth(token, 'password-session', int(time.time()) + 12 * 3600, credential)
        return {'token': token}

    @app.get('/auth/me')
    def me(token=Depends(owner)):
        return {'login': 'Bamb0oChen', 'role': 'owner'}

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
