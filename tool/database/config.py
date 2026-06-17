import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]

load_dotenv()

SUPPORTED_DB_TYPES = frozenset({"sqlite", "mysql"})


@dataclass(frozen=True)
class SQLiteConfig:
    db_type: str = "sqlite"
    path: Path = ROOT / "data" / "app.db"


@dataclass(frozen=True)
class MySQLConfig:
    db_type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str | None = None
    charset: str = "utf8mb4"
    ssl: bool = False
    ssl_ca: str | None = None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_sqlite_path() -> Path:
    raw = os.getenv("SQLITE_PATH", "./data/app.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _parse_mysql_url(url: str, database_override: str | None = None) -> MySQLConfig:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError(f"Unsupported MYSQL_URL scheme: {parsed.scheme}")

    database = database_override
    if database is None and parsed.path and parsed.path != "/":
        database = unquote(parsed.path.lstrip("/")) or None

    query = parse_qs(parsed.query)
    charset = query.get("charset", ["utf8mb4"])[0]

    return MySQLConfig(
        host=parsed.hostname or "localhost",
        port=parsed.port or 3306,
        user=unquote(parsed.username or "root"),
        password=unquote(parsed.password or ""),
        database=database,
        charset=charset,
        ssl=_parse_bool(os.getenv("DB_SSL")),
        ssl_ca=os.getenv("DB_SSL_CA") or None,
    )


def _load_mysql_config(database_override: str | None = None) -> MySQLConfig:
    mysql_url = os.getenv("MYSQL_URL", "").strip()
    if mysql_url:
        return _parse_mysql_url(mysql_url, database_override)

    database = database_override
    if database is None:
        raw_db = os.getenv("DB_NAME", "").strip()
        database = raw_db or None

    return MySQLConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=database,
        charset=os.getenv("DB_CHARSET", "utf8mb4"),
        ssl=_parse_bool(os.getenv("DB_SSL")),
        ssl_ca=os.getenv("DB_SSL_CA") or None,
    )


def load_config(
    db_type: str | None = None,
    database_override: str | None = None,
) -> SQLiteConfig | MySQLConfig:
    db_type = (db_type or os.getenv("DB_TYPE", "sqlite")).lower()
    if db_type not in SUPPORTED_DB_TYPES:
        raise ValueError(
            f"Unsupported database type: {db_type}. Supported: sqlite, mysql"
        )

    if db_type == "sqlite":
        return SQLiteConfig(path=_resolve_sqlite_path())

    return _load_mysql_config(database_override)
