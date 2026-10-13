#!/usr/bin/env python3
"""End-to-end smoke test: talks to the MCP servers over real stdio JSON-RPC.

Usage:
  python scripts/smoke_test.py search "посмотри новости за последнее время"
  python scripts/smoke_test.py fetch  "https://www.bbc.com/news/science-74120855"
  python scripts/smoke_test.py fetch  "https://example.com"   # Jina pass-through

Run with the same interpreter the servers will use, e.g. `.venv/bin/python`.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


async def run_mode(mode: str, argument: str) -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "epistemic_trap", mode],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"tools: {[t.name for t in tools.tools]}")
            if mode == "search":
                result = await session.call_tool("web_search", {"query": argument})
            else:
                result = await session.call_tool("web_fetch", {"url": argument})
            print("---")
            for block in result.content:
                print(getattr(block, "text", str(block))[:4000])
            return 0


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in {"search", "fetch"}:
        print(__doc__)
        return 2
    return asyncio.run(run_mode(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    raise SystemExit(main())
