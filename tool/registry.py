import functools
from typing import Any, Callable

from tool.current_time.time_util import get_current_time
from tool.current_time.weather import get_weather as _get_weather
from tool.current_time.region import get_region as _get_region
from tool.database.connection import connect as _db_connect
from tool.database.ddl import execute_sql as _db_execute_sql
from tool.fileoperator import create_file as _file_create
from tool.fileoperator import delete_file as _file_delete
from tool.fileoperator import read_file as _file_read
from tool.fileoperator import write_file as _file_write
from tool.news.fetcher import fetch_news
from tool.websearch.search import web_search as _web_search
from tool.scaffold import create_project as _create_project, post_init as _post_init
from tool.vault.store import (
    delete_entry,
    get_entry,
    list_entries,
    save_entry,
)

ToolHandler = Callable[..., Any]


def _wrap_result(fn: ToolHandler) -> ToolHandler:
    @functools.wraps(fn)
    def wrapper(**kwargs):
        try:
            data = fn(**kwargs)
            return {"success": True, "data": data}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
    return wrapper


@_wrap_result
def get_time(timezone: str = "Asia/Shanghai"):
    return get_current_time(timezone)


@_wrap_result
def get_weather(location: str | None = None):
    return _get_weather(location)


@_wrap_result
def get_region(location: str | None = None):
    return _get_region(location)


@_wrap_result
def get_news(
    category: str | None = None,
    lang: str | None = None,
    count: int = 10,
):
    return fetch_news(category=category, lang=lang, count=count)


@_wrap_result
def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
):
    return _web_search(query=query, max_results=max_results, search_depth=search_depth)


@_wrap_result
def create_project(project_name: str, project_type: str):
    result = _create_project(project_name, project_type)
    init_result = _post_init(project_name, project_type)
    result["post_init"] = init_result.get("steps", [])
    return result


@_wrap_result
def db_connect(db_type: str | None = None, database: str | None = None):
    return _db_connect(db_type, database)


@_wrap_result
def db_execute_sql(sql: str, confirm: bool = False):
    return _db_execute_sql(sql, confirm=confirm)


@_wrap_result
def vault_save(
    platform: str,
    username: str,
    password: str,
    user_confirmed: bool = False,
    note: str = "",
):
    return save_entry(platform, username, password, user_confirmed, note)


@_wrap_result
def vault_get(platform: str, reveal: bool = False):
    return get_entry(platform, reveal=reveal)


@_wrap_result
def vault_list():
    return list_entries()


@_wrap_result
def vault_delete(platform: str, user_confirmed: bool = False):
    return delete_entry(platform, user_confirmed)


@_wrap_result
def file_read(path: str, offset: int | None = None, limit: int | None = None):
    return _file_read(path, offset=offset, limit=limit)


@_wrap_result
def file_write(
    path: str,
    content: str | None = None,
    old_string: str | None = None,
    new_string: str | None = None,
    user_confirmed: bool = False,
):
    return _file_write(
        path,
        content=content,
        old_string=old_string,
        new_string=new_string,
        user_confirmed=user_confirmed,
    )


@_wrap_result
def file_create(path: str, is_directory: bool = False, content: str | None = None):
    return _file_create(path, is_directory=is_directory, content=content)


@_wrap_result
def file_delete(path: str, user_confirmed: bool = False):
    return _file_delete(path, user_confirmed=user_confirmed)


TOOL_REGISTRY: dict[str, ToolHandler] = {
    "get_weather": get_weather,
    "get_region": get_region,
    "get_time": get_time,
    "get_news": get_news,
    "web_search": web_search,
    "create_project": create_project,
    "db_connect": db_connect,
    "db_execute_sql": db_execute_sql,
    "vault_save": vault_save,
    "vault_get": vault_get,
    "vault_list": vault_list,
    "vault_delete": vault_delete,
    "file_read": file_read,
    "file_write": file_write,
    "file_create": file_create,
    "file_delete": file_delete,
}


TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location. Uses QWeather API. Supports global city lookup (configurable via QWEATHER_GEO_RANGE). Pass location name or omit for auto IP detection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or leave empty for auto IP detection",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_region",
        "description": "Get geographic region info for a location. Uses QWeather geo API. Supports global city lookup (configurable via QWEATHER_GEO_RANGE).",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or leave empty for auto IP detection",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_time",
        "description": "Get current date and time for a timezone. Works without external API keys.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone, e.g. Asia/Shanghai, America/New_York",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_news",
        "description": "Fetch today's news articles from RSS feeds. Categories: tech, finance, entertainment, politics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["tech", "finance", "entertainment", "politics"],
                    "description": "News category filter",
                },
                "lang": {
                    "type": "string",
                    "enum": ["zh", "en"],
                    "description": "Language filter",
                },
                "count": {
                    "type": "integer",
                    "description": "Max number of articles to return (default 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the internet for real-time information. "
            "Use when the user asks about current events, latest releases, prices, "
            "documentation, or anything not covered by local files or RSS news feeds. "
            "Do NOT use for predefined news categories (use get_news instead)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max number of results to return (default 5, max 10)",
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "basic=fast; advanced=more thorough but slower",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_project",
        "description": "Scaffold a new project. Supported types: vue3+vite, springboot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project directory to create",
                },
                "project_type": {
                    "type": "string",
                    "enum": ["vue3+vite", "springboot"],
                    "description": "Project template type",
                },
            },
            "required": ["project_name", "project_type"],
        },
    },
    {
        "name": "db_connect",
        "description": (
            "Connect to a database using .env configuration. "
            "SQLite: SQLITE_PATH (default ./data/app.db). "
            "MySQL 8.0+: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, "
            "or MYSQL_URL. Leave DB_NAME empty to connect without selecting a "
            "database (for CREATE DATABASE). Use database param to switch schema."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "db_type": {
                    "type": "string",
                    "enum": ["sqlite", "mysql"],
                    "description": "Database type (defaults to DB_TYPE in .env)",
                },
                "database": {
                    "type": "string",
                    "description": "Override DB_NAME for this session (MySQL only)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "db_execute_sql",
        "description": (
            "Execute a SQL statement against the active connection. "
            "Prefer one statement per call. "
            "Examples: CREATE DATABASE, CREATE TABLE, ALTER TABLE ADD/DROP/MODIFY COLUMN, "
            "SHOW TABLES, DESCRIBE table, SELECT. "
            "Destructive operations (DROP, DELETE, UPDATE, TRUNCATE, ALTER DROP/MODIFY/CHANGE) "
            "require confirm=true after user approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL statement(s) to execute",
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true for destructive SQL after user confirms",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "vault_save",
        "description": "Save platform credentials to encrypted local vault. Requires user_confirmed=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform or service name"},
                "username": {"type": "string", "description": "Account username or email"},
                "password": {"type": "string", "description": "Account password"},
                "user_confirmed": {
                    "type": "boolean",
                    "description": "Must be true after user explicitly approves saving",
                },
                "note": {"type": "string", "description": "Optional note"},
            },
            "required": ["platform", "username", "password"],
        },
    },
    {
        "name": "vault_get",
        "description": "Retrieve credentials for a platform. Password is masked by default.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name"},
                "reveal": {
                    "type": "boolean",
                    "description": "If true, return plaintext password (use sparingly)",
                },
            },
            "required": ["platform"],
        },
    },
    {
        "name": "vault_list",
        "description": "List all saved credential entries (no passwords returned).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "vault_delete",
        "description": "Delete credentials for a platform. Requires user_confirmed=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name"},
                "user_confirmed": {
                    "type": "boolean",
                    "description": "Must be true after user explicitly approves deletion",
                },
            },
            "required": ["platform"],
        },
    },
    {
        "name": "file_read",
        "description": "Read a UTF-8 text file within the workspace or AccessablePath roots. Supports large files via offset+limit (line-based streaming). Single response is capped by FILE_READ_MAX_RETURN_BYTES and FILE_READ_MAX_LINES (.env); default max 1000 lines when limit is omitted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to workspace or absolute under allowed roots)"},
                "offset": {"type": "integer", "description": "Start line (1-based, optional)"},
                "limit": {"type": "integer", "description": "Max lines to read (optional)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_write",
        "description": "Write a UTF-8 text file. Use content to overwrite, or old_string+new_string to patch. Config files require user_confirmed=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Full file content (overwrite mode)"},
                "old_string": {"type": "string", "description": "Text to replace (patch mode)"},
                "new_string": {"type": "string", "description": "Replacement text (patch mode)"},
                "user_confirmed": {
                    "type": "boolean",
                    "description": "Must be true when writing config files, after user approval",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_create",
        "description": "Create a new file or directory under the workspace or AccessablePath roots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to create"},
                "is_directory": {"type": "boolean", "description": "If true, create a directory"},
                "content": {"type": "string", "description": "Initial file content (files only)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_delete",
        "description": "Delete a file or directory. Always requires user_confirmed=true after user approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete"},
                "user_confirmed": {
                    "type": "boolean",
                    "description": "Must be true after user explicitly approves deletion",
                },
            },
            "required": ["path"],
        },
    },
]



def get_tool_schemas() -> list[dict]:
    return TOOL_SCHEMAS


def execute_tool(name: str, arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return {"success": False, "error": f"Unknown tool: {name}"}
    return handler(**arguments)
