import os
import time
from pathlib import Path

import jwt

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_KEY_PATH = ROOT / "qweather_key" / "ed25519-private.pem"
DEFAULT_JWT_TTL = 900
MAX_JWT_TTL = 86400
REFRESH_BUFFER_SEC = 60

_cached_token: str | None = None
_cached_exp: int = 0


def _load_private_key() -> str:
    key_path = os.getenv("QWEATHER_PRIVATE_KEY_PATH", "").strip()
    pem_path = Path(key_path) if key_path else DEFAULT_PRIVATE_KEY_PATH
    if not pem_path.is_absolute():
        pem_path = ROOT / pem_path

    if not pem_path.exists():
        raise ValueError(
            f"QWeather private key not found at {pem_path}. "
            "Set QWEATHER_PRIVATE_KEY_PATH or place ed25519-private.pem in qweather_key/"
        )
    return pem_path.read_text(encoding="utf-8")


def _get_kid() -> str:
    kid = os.getenv("QWEATHER_KID", "").strip()
    if not kid:
        raise ValueError("QWEATHER_KID is not configured")
    return kid


def _get_project_id() -> str:
    project_id = os.getenv("QWEATHER_PROJECT_ID", "").strip()
    if not project_id:
        raise ValueError("QWEATHER_PROJECT_ID is not configured")
    return project_id


def _get_jwt_ttl() -> int:
    raw = os.getenv("QWEATHER_JWT_TTL", str(DEFAULT_JWT_TTL)).strip()
    try:
        ttl = int(raw)
    except ValueError:
        ttl = DEFAULT_JWT_TTL
    return max(60, min(ttl, MAX_JWT_TTL))


def _generate_jwt() -> tuple[str, int]:
    private_key = _load_private_key()
    kid = _get_kid()
    project_id = _get_project_id()
    ttl = _get_jwt_ttl()

    iat = int(time.time()) - 30
    exp = iat + ttl
    payload = {"sub": project_id, "iat": iat, "exp": exp}
    headers = {"alg": "EdDSA", "kid": kid}

    token = jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)
    return token, exp


def get_auth_headers() -> dict[str, str]:
    global _cached_token, _cached_exp

    now = int(time.time())
    if _cached_token and _cached_exp - now > REFRESH_BUFFER_SEC:
        return {"Authorization": f"Bearer {_cached_token}"}

    token, exp = _generate_jwt()
    _cached_token = token
    _cached_exp = exp
    return {"Authorization": f"Bearer {token}"}
