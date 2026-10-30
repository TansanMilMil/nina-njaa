import secrets
import time

from repository._common import ConnectionProvider


class _AuthSessionMixin:
    def create_auth_session(self: ConnectionProvider, username: str, expires_at: int) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._connect() as con:
            con.execute(
                "INSERT INTO auth_sessions (id, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (session_id, username, int(time.time()), expires_at),
            )
        return session_id

    def get_auth_session(self: ConnectionProvider, session_id: str) -> dict | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT id, username, expires_at FROM auth_sessions WHERE id = ? AND expires_at > ?",
                (session_id, int(time.time())),
            ).fetchone()
        return dict(row) if row else None

    def delete_auth_session(self: ConnectionProvider, session_id: str) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM auth_sessions WHERE id = ?", (session_id,))

    def delete_expired_auth_sessions(self: ConnectionProvider) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (int(time.time()),))
