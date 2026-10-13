"""Entry point: `python -m epistemic_trap {search|fetch|selfcheck}`."""

from __future__ import annotations

import sys

USAGE = """Epistemic Trap — MCP red-team harness

Usage:
  python -m epistemic_trap search      run the web_search MCP server (stdio)
  python -m epistemic_trap fetch       run the web_fetch MCP server (stdio)
  python -m epistemic_trap selfcheck   validate corpus and simulate tool behaviour

Configuration is read from environment variables and an optional .env file.
See README.md and .env.example.
"""


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode in {"search", "fetch"}:
        from .config import load_config

        try:
            cfg = load_config(mode)
        except (FileNotFoundError, ValueError) as exc:
            print(f"epistemic-trap: configuration error: {exc}", file=sys.stderr)
            return 1

        if mode == "search":
            from .search_server import build_server
        else:
            from .fetch_server import build_server

        build_server(cfg).run()
        return 0

    if mode == "selfcheck":
        from .selfcheck import run

        return run(sys.argv[2:])

    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
