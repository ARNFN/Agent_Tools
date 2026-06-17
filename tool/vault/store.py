import json
from pathlib import Path

from tool.vault.crypto import decrypt, encrypt, mask_password

ROOT = Path(__file__).resolve().parents[2]
VAULT_PATH = ROOT / "data" / "vault.json"


def _load() -> dict:
    if not VAULT_PATH.exists():
        return {}
    with open(VAULT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_entry(
    platform: str,
    username: str,
    password: str,
    user_confirmed: bool = False,
    note: str = "",
) -> dict:
    if not user_confirmed:
        raise PermissionError(
            "Saving credentials requires user_confirmed=true after explicit user approval."
        )

    data = _load()
    entry_id = platform.lower().replace(" ", "_")
    data[entry_id] = {
        "platform": platform,
        "username": username,
        "password_enc": encrypt(password),
        "note": note,
    }
    _save(data)
    return {
        "id": entry_id,
        "platform": platform,
        "username": username,
        "password": mask_password(password),
        "note": note,
    }


def get_entry(platform: str, reveal: bool = False) -> dict:
    data = _load()
    entry_id = platform.lower().replace(" ", "_")
    if entry_id not in data:
        raise KeyError(f"No credentials found for platform: {platform}")

    entry = data[entry_id]
    password = decrypt(entry["password_enc"])
    return {
        "id": entry_id,
        "platform": entry["platform"],
        "username": entry["username"],
        "password": password if reveal else mask_password(password),
        "note": entry.get("note", ""),
    }


def list_entries() -> list[dict]:
    data = _load()
    return [
        {
            "id": eid,
            "platform": entry["platform"],
            "username": entry["username"],
            "note": entry.get("note", ""),
        }
        for eid, entry in data.items()
    ]


def delete_entry(platform: str, user_confirmed: bool = False) -> dict:
    if not user_confirmed:
        raise PermissionError(
            "Deleting credentials requires user_confirmed=true after explicit user approval."
        )

    data = _load()
    entry_id = platform.lower().replace(" ", "_")
    if entry_id not in data:
        raise KeyError(f"No credentials found for platform: {platform}")

    removed = data.pop(entry_id)
    _save(data)
    return {"id": entry_id, "platform": removed["platform"], "deleted": True}
