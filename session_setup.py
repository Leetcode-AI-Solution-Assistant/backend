from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Query, Request
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier

from models import SessionData

cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",  # use env var in prod
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


async def resolve_session_id(
    request: Request,
    session_id_header: str | None = Header(default=None, alias="X-Session-ID"),
    session_id_query: UUID | None = Query(default=None, alias="session_id"),
) -> UUID:
    """Find a session id from header, query string, or cookie."""
    if session_id_header:
        try:
            return UUID(session_id_header)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-Session-ID header") from exc

    if session_id_query:
        return session_id_query

    cookie_value = request.cookies.get(cookie.cookie_name)
    if cookie_value:
        try:
            return UUID(cookie_value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid session cookie") from exc

    raise HTTPException(
        status_code=401,
        detail=(
            "Session id missing. Provide X-Session-ID header, session_id query param, "
            "or reuse the session cookie returned by /create_session."
        ),
    )


@dataclass
class SessionContext:
    id: UUID
    data: SessionData


async def get_session_context(
    request: Request,
    session_id: UUID = Depends(resolve_session_id),
    session_auth: str | None = Header(default=None, alias="X-Session-Auth"),
) -> SessionContext:
    """Load the session and require an auth token to guard against spoofed IDs."""
    session = await backend.read(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    expected = session.auth_token
    # Cookie-only flows still need to present the token to prevent hijack by guessing the ID.
    provided = session_auth or request.cookies.get("session_auth")
    if not provided or provided != expected:
        raise HTTPException(status_code=403, detail="Invalid session auth token")

    return SessionContext(id=session_id, data=session)
