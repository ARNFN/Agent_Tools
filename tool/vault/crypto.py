import base64
import os

from cryptography.fernet import Fernet, InvalidToken


def _get_key() -> bytes:
    raw = os.getenv("VAULT_KEY", "")
    if not raw:
        raise ValueError("VAULT_KEY is not configured")
    try:
        return raw.encode() if isinstance(raw, str) else raw
    except Exception as exc:
        raise ValueError("Invalid VAULT_KEY format") from exc


def get_fernet() -> Fernet:
    return Fernet(_get_key())


def encrypt(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed — wrong VAULT_KEY or corrupted data") from exc


def generate_key() -> str:
    return Fernet.generate_key().decode()


def mask_password(password: str) -> str:
    if len(password) <= 2:
        return "*" * len(password)
    return password[0] + "*" * (len(password) - 2) + password[-1]
