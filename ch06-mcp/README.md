# Chapter 6 — MCP: the standard plug for tools and context

**Video:** _link added on release_ · **Length:** ~15 min

Write a tool once, use it in every agent.

| File | What it shows |
| --- | --- |
| [`server.py`](server.py) | An MCP server (Python SDK, FastMCP) exposing `search_repo` and `read_file` |
| [`client_agent.py`](client_agent.py) | Our own harness discovering and calling the server's tools |
| [`claude-code.mcp.json`](claude-code.mcp.json) | The same server plugged into Claude Code |

```bash
python ch06-mcp/client_agent.py "Where is the planted bug?"
```

## Plug it into Claude Code

Copy `claude-code.mcp.json` to `.mcp.json` at the root of a project (edit the absolute paths), or run:

```bash
claude mcp add repo-assistant -- python /absolute/path/to/ch06-mcp/server.py
```

Every MCP server you connect adds its tool definitions to the context window: connect only the ones you need.

References: [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk), [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).
