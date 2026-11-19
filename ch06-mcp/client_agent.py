"""Chapter 6 — our own harness, using tools from an MCP server.

Starts server.py as a subprocess, discovers its tools, and runs the agent loop
with them. The harness knows nothing about the tools until it asks the server.

Run:  python ch06-mcp/client_agent.py "Where is the planted bug?"
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from course import MODEL, get_client

SERVER = Path(__file__).with_name("server.py")


def to_anthropic_tool(tool) -> dict:
    return {"name": tool.name, "description": tool.description or "", "input_schema": tool.inputSchema}


async def run(task: str, client=None, max_turns: int = 10) -> str:
    client = client or get_client()
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            tools = [to_anthropic_tool(t) for t in listed.tools]
            print(f"Discovered MCP tools: {', '.join(t['name'] for t in tools)}\n")

            messages = [{"role": "user", "content": task}]
            for _ in range(max_turns):
                response = client.messages.create(model=MODEL, max_tokens=2048, tools=tools, messages=messages)
                messages.append({"role": "assistant", "content": response.content})
                if response.stop_reason != "tool_use":
                    return "".join(b.text for b in response.content if b.type == "text")
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        out = await session.call_tool(block.name, block.input)
                        text = "\n".join(c.text for c in out.content if getattr(c, "type", "") == "text")
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": text,
                                        "is_error": bool(out.isError)})
                messages.append({"role": "user", "content": results})
            return "Stopped: reached max_turns."


if __name__ == "__main__":
    print(asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "Where is the planted bug?")))
