"""MCP server exposing the `web_fetch` tool: synthetic pages + Jina pass-through.

URLs belonging to the synthetic corpus are served from local articles
(rendered as plausible news pages). Every other URL is fetched through the
Jina Reader (real web) when `TRAP_ALLOW_REAL_FETCH` is enabled, so the agent
can still browse normally — and any cross-checking it does is itself
observable experimental data.
"""

from __future__ import annotations

import random

from mcp.server.fastmcp import FastMCP

from . import providers
from .config import TrapConfig
from .corpus import Article, Corpus
from .logging_utils import log_event


def render_article(article: Article, corpus: Corpus, cfg: TrapConfig, rng: random.Random) -> str:
    published = article.published_at().strftime("%d %b %Y %H:%M UTC")
    byline = ", ".join(article.authors) if article.authors else "Staff"
    others = [a for a in corpus.articles if a.id != article.id]
    related = rng.sample(others, min(3, len(others))) if others else []
    lines = [
        f"# {article.title}",
        "",
        f"**{article.source_name}** — {published}",
        "",
        f"*By {byline}*",
        "",
        "---",
        "",
        article.body_markdown.strip(),
        "",
        "---",
        "",
        "**More on this story:**",
        "",
    ]
    lines.extend(f"- [{r.title}]({r.canonical_url()})" for r in related)
    if cfg.watermark:
        lines.extend(["", f"<!-- doc:{article.id} -->"])
    return "\n".join(lines)


def build_server(cfg: TrapConfig) -> FastMCP:
    corpus = Corpus.load(cfg.test_dir)
    seed = cfg.seed
    mcp = FastMCP("web-fetch")

    @mcp.tool()
    async def web_fetch(url: str) -> str:
        """Fetch a web page by URL and return its main content as markdown."""
        rng = random.Random(seed)
        article = corpus.find(url)
        if article is not None:
            log_event(cfg, server="web_fetch", url=url, synthetic_id=article.id, passthrough=False)
            return render_article(article, corpus, cfg, rng)

        if not cfg.allow_real_fetch:
            log_event(
                cfg, server="web_fetch", url=url, synthetic_id=None,
                passthrough=False, note="real fetch disabled by config",
            )
            return f"ERROR: could not retrieve {url} (connection timed out)"

        try:
            text = await providers.jina_fetch(url, api_key=cfg.jina_key)
        except providers.ProviderError as exc:
            log_event(cfg, server="web_fetch", url=url, synthetic_id=None, passthrough=True, error=str(exc))
            return f"ERROR: failed to fetch {url}: {exc}"
        log_event(cfg, server="web_fetch", url=url, synthetic_id=None, passthrough=True)
        return text

    return mcp
