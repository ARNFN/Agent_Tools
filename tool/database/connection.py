import sqlite3
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from tool.database.config import MySQLConfig, SQLiteConfig, load_config

_active_connection = None
_active_type = None


def _connect_sqlite(cfg: SQLiteConfig) -> dict:
    cfg.path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(cfg.path))
    conn.row_factory = sqlite3.Row
    return conn, {"db_type": "sqlite", "path": str(cfg.path), "connected": True}


def _connect_mysql(cfg: MySQLConfig) -> dict:
    kwargs = {
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "charset": cfg.charset,
        "cursorclass": DictCursor,
        "autocommit": False,
    }
    if cfg.database:
        kwargs["database"] = cfg.database
    if cfg.ssl:
        kwargs["ssl"] = {"ca": cfg.ssl_ca} if cfg.ssl_ca else {}

    try:
        conn = pymysql.connect(**kwargs)
    except pymysql.MySQLError as exc:
        raise ConnectionError(
            f"MySQL connection failed ({cfg.host}:{cfg.port}, user={cfg.user}): {exc}"
        ) from exc

    conn.ping(reconnect=True)
    return conn, {
        "db_type": "mysql",
        "host": cfg.host,
        "port": cfg.port,
        "database": cfg.database,
        "connected": True,
    }


def connect(db_type: str | None = None, database: str | None = None) -> dict:
    global _active_connection, _active_type

    cfg = load_config(db_type, database_override=database)

    if _active_connection is not None:
        try:
            _active_connection.close()
        except Exception:
            pass
        _active_connection = None
        _active_type = None

    if isinstance(cfg, SQLiteConfig):
        _active_connection, info = _connect_sqlite(cfg)
        _active_type = "sqlite"
        return info

    _active_connection, info = _connect_mysql(cfg)
    _active_type = "mysql"
    return info


def get_connection():
    global _active_connection, _active_type
    if _active_connection is None:
        connect()
    return _active_connection, _active_type


@contextmanager
def cursor():
    conn, db_type = get_connection()
    cur = conn.cursor()
    try:
        yield cur, db_type
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
