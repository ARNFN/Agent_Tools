

import json

import os

import sys



import anthropic

from dotenv import load_dotenv



from tool import execute_tool, get_tool_schemas

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False



load_dotenv()



API_KEY = ""  # 留空则从环境变量/.env 读取

BASE_URL = ""  # 留空则从 ANTHROPIC_BASE_URL 读取



SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools for weather, time, news, web search, project scaffolding, database management, credential vault, and file operations.

Tool selection:
- get_news: today's headlines from fixed RSS feeds (tech/finance/entertainment/politics).
- web_search: open-ended internet search for specific questions, latest info, docs, prices, etc.
- When answering from web_search results, cite source URLs when helpful.
- If search results are insufficient, refine the query and search again (at most 2 retries).

Important safety rules:

- For destructive database operations (DROP, DELETE, UPDATE, TRUNCATE, ALTER DROP/MODIFY/CHANGE), you MUST ask the user for confirmation first, then pass confirm=true only after they approve.

- Before database operations, call db_connect. For MySQL use db_type=mysql. To create a database when none is selected, connect with DB_NAME empty (or omit database), then run CREATE DATABASE, then db_connect again with database set.

- Never expose DB_PASSWORD or other database credentials in chat.

- For vault write operations (vault_save, vault_delete), you MUST ask the user for explicit approval first, then pass user_confirmed=true only after they confirm.

- Never expose vault passwords in chat unless the user explicitly requests reveal=true.

- When a project directory already exists, suggest the user pick a different name.

- File tools default to the project workspace (repository root). Paths outside it require AccessablePath=... entries in .env (one path per line). Do not access unconfigured external paths.

- For file_write on config files (.env, config/*, *.yaml, application.properties, pom.xml, etc.), ask the user first, then pass user_confirmed=true.

- For any file_delete, ask the user first, then pass user_confirmed=true.

- Do not paste secrets from .env or credential files into chat; summarize or redact sensitive values.

Formatting rules:
- Use Markdown for structured answers (headings, tables, bold).
- For comparisons, use Markdown tables with header and separator rows.
- Use ### for section headings and --- between major sections.

"""



MAX_ROUNDS = 10


def _is_rich_enabled() -> bool:
    return os.getenv("ENABLE_RICH", "").strip().lower() == "enable"


def render_response(text: str) -> None:
    if _is_rich_enabled() and _RICH_AVAILABLE:
        console = Console(highlight=False)
        console.print(
            Panel(
                Markdown(text),
                title="Assistant",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        print()
        return

    if _is_rich_enabled() and not _RICH_AVAILABLE:
        print("Rich not installed, falling back to plain output", file=sys.stderr)

    print(f"Assistant: {text}\n")





def _get_client() -> anthropic.Anthropic:

    key = API_KEY or os.getenv("ANTHROPIC_API_KEY")

    base_url = BASE_URL or os.getenv("ANTHROPIC_BASE_URL")

    kwargs = {"api_key": key}

    if base_url:

        kwargs["base_url"] = base_url

    return anthropic.Anthropic(**kwargs)





def handle_tool_calls(content_blocks) -> tuple[list[dict], bool]:

    tool_results = []

    has_tool_use = False



    for block in content_blocks:

        if block.type == "tool_use":

            has_tool_use = True

            result = execute_tool(block.name, block.input)

            tool_results.append(

                {

                    "type": "tool_result",

                    "tool_use_id": block.id,

                    "content": json.dumps(result, ensure_ascii=False),

                }

            )



    return tool_results, has_tool_use





def _default_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "").strip()


def run_agent(

    user_message: str,

    messages: list[dict] | None = None,

    model: str | None = None,

) -> str:

    client = _get_client()

    tools = get_tool_schemas()

    resolved_model = model or _default_model()
    if not resolved_model:
        return "ANTHROPIC_MODEL is not configured. Set it in .env (see .env.example)."

    if messages is None:

        messages = []



    messages.append({"role": "user", "content": user_message})



    for _ in range(MAX_ROUNDS):

        try:

            response = client.messages.create(

                model=resolved_model,

                max_tokens=4096,

                system=SYSTEM_PROMPT,

                tools=tools,
                
                messages=messages,

            )

        except Exception as exc:

            return f"API 请求失败: {exc}"



        if response.stop_reason != "tool_use":

            texts = [b.text for b in response.content if hasattr(b, "text")]

            reply = "\n".join(texts)

            messages.append({"role": "assistant", "content": response.content})

            return reply



        tool_results, _ = handle_tool_calls(response.content)

        messages.append({"role": "assistant", "content": response.content})

        messages.append({"role": "user", "content": tool_results})



    reply = "Max tool-use rounds reached."

    messages.append({"role": "assistant", "content": reply})

    return reply





def interactive_chat(model: str | None = None) -> None:

    messages: list[dict] = []

    print("Interactive chat (type 'exit', 'quit', or 'q' to leave)\n")



    while True:

        try:

            user_input = input("You: ").strip()

        except (EOFError, KeyboardInterrupt):

            print("\nBye!")

            break



        if user_input.lower() in ("exit", "quit", "q"):

            break

        if not user_input:

            continue



        response = run_agent(user_input, messages=messages, model=model or _default_model())

        render_response(response)





def _configure_stdout() -> None:

    if hasattr(sys.stdout, "reconfigure"):

        try:

            sys.stdout.reconfigure(encoding="utf-8")

        except Exception:

            pass





def main():

    _configure_stdout()

    if len(sys.argv) > 1:

        prompt = " ".join(sys.argv[1:])

        render_response(run_agent(prompt))

    else:

        interactive_chat()





if __name__ == "__main__":

    main()


