import os
from pathlib import Path
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio, create_static_tool_filter
from .market import massive_api_key

load_dotenv(override=True)

PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
TIMEOUT = 120


def _env(*extra: dict | None) -> dict[str, str]:
    """Full process env plus extras. A tiny env dict would hide PATH and break npx/uvx."""
    merged = {k: str(v) for k, v in os.environ.items() if v is not None}
    for blob in extra:
        if not blob:
            continue
        for key, value in blob.items():
            if value is not None:
                merged[str(key)] = str(value)
    return merged


def _stdio(name: str, params: dict, **kwargs) -> MCPServerStdio:
    return MCPServerStdio(params, name=name, client_session_timeout_seconds=TIMEOUT, **kwargs)


# Local market MCP uses backend.market.get_share_price: Massive previous-close on a free
# key, simulator otherwise. Massive's own MCP (uvx mcp_massive) needs mcp<2.0.0 and last-trade
# is paid; opt in with USE_MASSIVE_MCP=1.
if massive_api_key and os.getenv("USE_MASSIVE_MCP") == "1":
    market_params = {
        "command": "uvx",
        "args": [
            "--with",
            "mcp<2.0.0",
            "--from",
            "git+https://github.com/massive-com/mcp_massive@v0.10.0",
            "mcp_massive",
        ],
        "env": _env({"MASSIVE_API_KEY": massive_api_key}),
    }
else:
    market_params = {
        "command": "uv",
        "args": ["run", "-m", "backend.market_server"],
        "cwd": PROJECT_DIR,
        "env": _env(),
    }


def trader_mcp_servers() -> list[MCPServerStdio]:
    """The trader's MCP servers: our Accounts server, Push Notification and Market data."""
    return [
        _stdio("accounts", {"command": "uv", "args": ["run", "-m", "backend.accounts_server"], "cwd": PROJECT_DIR, "env": _env()}),
        _stdio("push", {"command": "uv", "args": ["run", "-m", "backend.push_server"], "cwd": PROJECT_DIR, "env": _env()}),
        _stdio("market", market_params),
    ]


def researcher_mcp_servers(name: str) -> list[MCPServerStdio]:
    """The researcher's MCP servers: Fetch, Tavily web search and Memory.

    Tavily's server offers several tools; we restrict it to web search so the
    researcher reaches for plain search rather than its heavier crawl or deep-research tools.
    """
    tavily_key = os.getenv("TAVILY_API_KEY") or ""
    fetch = _stdio("fetch", {"command": "uvx", "args": ["--with", "mcp<2", "mcp-server-fetch"], "env": _env()})
    search = _stdio(
        "tavily",
        {"command": "npx", "args": ["-y", "tavily-mcp@latest"], "env": _env({"TAVILY_API_KEY": tavily_key})},
        tool_filter=create_static_tool_filter(allowed_tool_names=["tavily_search"]),
    )
    memory = _stdio(
        "memory",
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "cwd": PROJECT_DIR,
            "env": _env({"LIBSQL_URL": f"file:./memory/{name}.db"}),
        },
    )
    return [fetch, search, memory]
