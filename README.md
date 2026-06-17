# Python-Agent

Anthropic-compatible **agent tools** for Python: weather, time, news, web search, project scaffolding, database ops, encrypted vault, and sandboxed file I/O.

This repository provides **tools only** (`tool/` + `tool/registry.py`). [`llm.py`](llm.py) is an optional demo client that calls an external LLM via the Anthropic SDK—it is not bundled with any model.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env   # then fill in your keys
python llm.py
```

## Tools

| Tool | Description |
|------|-------------|
| `get_time` | Current time by timezone |
| `get_weather` / `get_region` | QWeather (optional) |
| `get_news` | RSS headlines by category |
| `web_search` | Tavily search (optional) |
| `create_project` | Vue3+Vite / Spring Boot scaffolds |
| `db_connect` / `db_execute_sql` | MySQL etc. (optional) |
| `vault_*` | Local encrypted credential store |
| `file_read` / `file_write` / `file_create` / `file_delete` | Sandboxed file ops |

Tool schemas live in [`tool/registry.py`](tool/registry.py). Import in your own agent:

```python
from tool import execute_tool, get_tool_schemas
```

## Configuration

Copy [`.env.example`](.env.example) to `.env`. **Never commit `.env`.**

- `ANTHROPIC_*` — required only for the `llm.py` demo client
- `AccessablePath` — extra directories for file tools (one path per line)
- See `.env.example` for QWeather, Tavily, DB, and vault settings

## License

See repository license (add if needed).
