"""Epistemic Trap — a red-team harness probing tool-source credulity of LLM coding agents.

Ships two MCP servers (`web_search`, `web_fetch`) that behave like a normal
web-access stack but inject controlled synthetic news coverage, so a researcher
can measure whether an agent trusts tool output over its own knowledge.
"""

__version__ = "0.1.0"
