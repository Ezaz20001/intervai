import re
import os
import time
import hashlib
import secrets
import logging
import threading
from pathlib import Path
from typing import Optional
from functools import wraps

logger = logging.getLogger("security")

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_user_id(user_id: str) -> str:
    if not user_id or not USER_ID_PATTERN.match(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID. Only alphanumeric, dash, and underscore allowed (1-64 chars).",
        )
    return user_id


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^\w.\-]", "_", name)
    name = re.sub(r"\.{2,}", ".", name)
    if not name or name.startswith("."):
        name = "upload" + secrets.token_hex(4)
    return name[:255]


def validate_file_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return ext


def validate_file_size(size: int) -> None:
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )


def safe_path(base_dir: Path, filename: str) -> Path:
    resolved = (base_dir / filename).resolve()
    if not str(resolved).startswith(str(base_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    return resolved


_API_KEYS: dict = {}


def register_api_key(name: str) -> str:
    key = "ak_" + secrets.token_hex(32)
    _API_KEYS[key] = {"name": name, "created": time.time()}
    return key


def load_api_keys_from_env() -> dict:
    raw = os.getenv("API_KEYS", "")
    if raw:
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                name, key = pair.split(":", 1)
                _API_KEYS[key.strip()] = {"name": name.strip(), "created": time.time()}
    return _API_KEYS


def require_api_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token in _API_KEYS:
            return _API_KEYS[token]["name"]
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() if request.headers.get("X-Forwarded-For") else (request.client.host if request.client else "unknown")
    logger.warning(f"Failed auth attempt from {client_ip}")
    raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


_session_tokens: dict = {}


def create_session_token(user_id: str) -> str:
    token = generate_session_token()
    _session_tokens[token] = {
        "user_id": user_id,
        "created": time.time(),
        "expires": time.time() + 3600 * 8,
    }
    logger.info(f"Session token created for user={user_id}")
    return token


def validate_session_token(token: str) -> str:
    info = _session_tokens.get(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    if time.time() > info["expires"]:
        del _session_tokens[token]
        raise HTTPException(status_code=401, detail="Session expired.")
    return info["user_id"]


def cleanup_expired_tokens():
    now = time.time()
    expired = [k for k, v in _session_tokens.items() if now > v["expires"]]
    for k in expired:
        del _session_tokens[k]


def _start_token_cleanup_daemon():
    def _loop():
        while True:
            time.sleep(300)
            cleanup_expired_tokens()
            rate_limiter.cleanup()
    t = threading.Thread(target=_loop, daemon=True)
    t.start()

_start_token_cleanup_daemon()


class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            if key not in self._requests:
                self._requests[key] = []
            self._requests[key] = [
                t for t in self._requests[key] if now - t < self.window
            ]
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True

    def cleanup(self):
        now = time.time()
        with self._lock:
            empty = [
                k
                for k, v in self._requests.items()
                if not v or now - v[-1] > self.window * 2
            ]
            for k in empty:
                del self._requests[k]


rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


def rate_limit(request: Request):
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    if not rate_limiter.check(client_ip):
        logger.info(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")


class SessionManager:
    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: dict = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def create(self, session_id: int, user_id: str, orchestrator) -> None:
        with self._lock:
            self._sessions[session_id] = {
                "orchestrator": orchestrator,
                "user_id": user_id,
                "created": time.time(),
                "last_active": time.time(),
            }

    def get(self, session_id: int, user_id: str = None):
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            if time.time() - session["last_active"] > self._ttl:
                self._cleanup_session(session_id)
                return None
            if user_id and session["user_id"] != user_id:
                return None
            session["last_active"] = time.time()
            return session["orchestrator"]

    def remove(self, session_id: int) -> None:
        with self._lock:
            self._cleanup_session(session_id)

    def _cleanup_session(self, session_id: int) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            try:
                session["orchestrator"].end_session()
            except Exception:
                pass

    def cleanup_stale(self) -> None:
        now = time.time()
        with self._lock:
            stale = [
                sid
                for sid, s in self._sessions.items()
                if now - s["last_active"] > self._ttl
            ]
            for sid in stale:
                self._cleanup_session(sid)

    def get_owner(self, session_id: int) -> Optional[str]:
        with self._lock:
            session = self._sessions.get(session_id)
            return session["user_id"] if session else None


session_manager = SessionManager(ttl_seconds=3600)
