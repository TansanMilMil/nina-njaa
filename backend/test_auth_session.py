import os
import sqlite3
import tempfile
import time
import unittest

_tmpdir = tempfile.TemporaryDirectory()
_db_path = os.path.join(_tmpdir.name, "recipes.db")
sqlite3.connect(_db_path).close()
os.environ.update(
    {
        "NINA_NJAA_DB_PATH": _db_path,
        "NINA_NJAA_JWT_SECRET_KEY": "test-secret-key-for-unit-tests-only-32b",
        "NINA_NJAA_GOOGLE_CLIENT_ID": "client-id",
        "NINA_NJAA_GOOGLE_CLIENT_SECRET": "client-secret",
        "NINA_NJAA_GOOGLE_REDIRECT_URI": "http://localhost/callback",
        "NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS": "me@example.com=alice",
        "NINA_NJAA_SECURE_COOKIE": "false",
    }
)

import jwt
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from db import repo
from routers import auth


def login_cookie(username="alice") -> str:
    response = Response()
    auth.start_session(response, username)
    header = response.headers["set-cookie"]
    return header.split(";", 1)[0].split("=", 1)[1]


class AuthSessionTest(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router)
        self.client = TestClient(app)

    def me(self, token):
        self.client.cookies.clear()
        self.client.cookies.set(auth.AUTH_COOKIE, token)
        return self.client.get("/api/auth/me")

    def test_login_token_is_accepted(self):
        res = self.me(login_cookie())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"username": "alice"})

    def test_logout_revokes_stolen_token(self):
        token = login_cookie()
        self.client.cookies.set(auth.AUTH_COOKIE, token)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(self.me(token).status_code, 401)

    def test_logout_keeps_other_sessions(self):
        token = login_cookie()
        other = login_cookie()
        self.client.cookies.set(auth.AUTH_COOKIE, token)
        self.client.post("/api/auth/logout")
        self.assertEqual(self.me(other).status_code, 200)

    def test_token_without_session_is_rejected(self):
        legacy = jwt.encode(
            {"sub": "alice", "exp": int(time.time()) + 3600}, auth.JWT_SECRET_KEY, algorithm=auth.JWT_ALGORITHM
        )
        self.assertEqual(self.me(legacy).status_code, 401)

    def test_token_with_other_username_is_rejected(self):
        payload = jwt.decode(login_cookie(), auth.JWT_SECRET_KEY, algorithms=[auth.JWT_ALGORITHM])
        payload["sub"] = "mallory"
        forged = jwt.encode(payload, auth.JWT_SECRET_KEY, algorithm=auth.JWT_ALGORITHM)
        self.assertEqual(self.me(forged).status_code, 401)

    def test_expired_session_is_rejected(self):
        session_id = repo.create_auth_session("alice", int(time.time()) - 1)
        token = jwt.encode(
            {"sub": "alice", "sid": session_id, "exp": int(time.time()) + 3600},
            auth.JWT_SECRET_KEY,
            algorithm=auth.JWT_ALGORITHM,
        )
        self.assertEqual(self.me(token).status_code, 401)

    def test_refresh_does_not_extend_past_session_expiry(self):
        expires_at = int(time.time()) + 60
        session_id = repo.create_auth_session("alice", expires_at)
        response = Response()
        auth.set_session_cookie(response, {"id": session_id, "username": "alice", "expires_at": expires_at})
        token = response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]
        payload = jwt.decode(token, auth.JWT_SECRET_KEY, algorithms=[auth.JWT_ALGORITHM])
        self.assertLessEqual(payload["exp"], expires_at)
        self.assertIn("Max-Age=", response.headers["set-cookie"])

    def test_login_purges_expired_sessions(self):
        session_id = repo.create_auth_session("alice", int(time.time()) - 1)
        login_cookie()
        with repo._connect() as con:
            row = con.execute("SELECT 1 FROM auth_sessions WHERE id = ?", (session_id,)).fetchone()
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
