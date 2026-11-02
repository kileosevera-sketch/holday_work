"""Single-admin login and short-lived signed access tokens."""
import base64
import hashlib
import hmac
import os
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
TOKEN_LIFETIME_SECONDS = 12 * 60 * 60
AUTH_CONFIG_FILE = Path(__file__).with_name(".env")


def _read_local_config() -> dict[str, str]:
    if not AUTH_CONFIG_FILE.is_file():
        return {}

    values = {}
    for line in AUTH_CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def _setting(name: str) -> str:
    return _read_local_config().get(name, os.environ.get(name, ""))


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=2000)


def _token_secret() -> bytes | None:
    secret = _setting("APP_AUTH_SECRET")
    return secret.encode("utf-8") if len(secret) >= 32 else None


def verify_access_token(token: str) -> bool:
    secret = _token_secret()
    username = _setting("APP_USERNAME")
    if not secret or not username:
        return False

    try:
        encoded_payload, provided_signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(provided_signature, expected_signature):
            return False

        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        token_username, expires_at = payload_bytes.decode("utf-8").rsplit("|", 1)
        return (
            hmac.compare_digest(token_username, username)
            and int(expires_at) > int(time.time())
        )
    except (ValueError, UnicodeDecodeError):
        return False


@router.post("/login")
def login(credentials: LoginRequest):
    username = _setting("APP_USERNAME")
    password = _setting("APP_PASSWORD")
    secret = _token_secret()
    if not username or not password or not secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Login is not configured. Set APP_USERNAME, APP_PASSWORD, and "
                "APP_AUTH_SECRET (at least 32 characters) in the backend environment."
            ),
        )

    username_matches = hmac.compare_digest(
        credentials.username.encode("utf-8"), username.encode("utf-8")
    )
    password_matches = hmac.compare_digest(
        credentials.password.encode("utf-8"), password.encode("utf-8")
    )
    if not username_matches or not password_matches:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid username or password. Check APP_USERNAME and APP_PASSWORD "
                "in backend/.env."
            ),
        )

    expires_at = int(time.time()) + TOKEN_LIFETIME_SECONDS
    payload = f"{username}|{expires_at}".encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(
        secret, encoded_payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return {
        "access_token": f"{encoded_payload}.{signature}",
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_SECONDS,
    }
