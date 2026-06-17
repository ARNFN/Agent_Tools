# Python-Agent

面向 Python 的 **Agent 工具集**，工具定义兼容 Anthropic Tool Use 格式。

本仓库**只提供工具实现**（`tool/` 与 `tool/registry.py`），**不包含任何 LLM 模型**。[`llm.py`](llm.py) 是一个可选的演示客户端，通过 Anthropic SDK 调用外部 API，便于本地试跑。

---

## 功能概览

| 类别 | 工具 | 说明 |
|------|------|------|
| 时间与天气 | `get_time` | 按时区返回当前时间 |
| | `get_weather` / `get_region` | 和风天气（需配置，可选） |
| 信息检索 | `get_news` | 按分类抓取 RSS 头条 |
| | `web_search` | Tavily 网页搜索（需配置，可选） |
| 工程脚手架 | `create_project` | 生成 Vue3+Vite 或 Spring Boot 项目 |
| 数据库 | `db_connect` / `db_execute_sql` | MySQL 等连接与 SQL 执行（需配置，可选） |
| 凭据保险库 | `vault_save` / `vault_get` / `vault_list` / `vault_delete` | 本地加密存储敏感信息 |
| 文件操作 | `file_read` / `file_write` / `file_create` / `file_delete` | 沙箱内读写，支持路径白名单 |

所有工具的 Schema 定义见 [`tool/registry.py`](tool/registry.py)。

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

编辑 `.env`，填入所需 API Key 与路径。**切勿将 `.env` 提交到 Git。**

### 3. 运行演示客户端（可选）

```bash
python llm.py
```

---

## 接入自己的 Agent

```python
from tool import execute_tool, get_tool_schemas

# 将 get_tool_schemas() 的返回值传给 LLM 的 tools 参数
schemas = get_tool_schemas()

# LLM 返回 tool_use 后，调用 execute_tool 执行
result = execute_tool("get_time", {"timezone": "Asia/Shanghai"})
# result: {"success": True, "data": ...} 或 {"success": False, "error": "..."}
```

---

## 配置说明

复制 [`.env.example`](.env.example) 为 `.env` 后，按需填写以下项：

| 变量 | 用途 |
|------|------|
| `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` | 仅 `llm.py` 演示客户端需要 |
| `QWEATHER_*` | 天气与地理区域工具（可选） |
| `TAVILY_API_KEY` | 网页搜索（可选） |
| `DB_*` | 数据库工具（可选） |
| `VAULT_KEY` | 本地凭据保险库加密密钥 |
| `AccessablePath` | 文件工具可访问的额外目录，每行一个路径 |
| `FILE_READ_MAX_RETURN_BYTES` / `FILE_READ_MAX_LINES` | 文件读取上限（可选） |

和风天气 Ed25519 私钥放置方式见 [`qweather_key/README.md`](qweather_key/README.md)。

脚手架默认参数见 [`config/scaffold_defaults.yaml`](config/scaffold_defaults.yaml)。

---

## 目录结构

```
.
├── tool/              # 各工具实现
│   └── registry.py    # 工具注册与 Schema
├── config/            # RSS 源、脚手架默认配置
├── llm.py             # 可选演示客户端
├── .env.example       # 环境变量模板（无密钥）
└── requirements.txt
```

本地生成物（如 `projects/`、`.venv/`、`.env`）已在 `.gitignore` 中排除，不会进入版本库。

---

## 许可证

[MIT License](LICENSE)
