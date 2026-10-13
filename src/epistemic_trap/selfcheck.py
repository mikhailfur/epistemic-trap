"""Offline self-check: validates configuration + corpus and simulates tool behaviour.

Run:  python -m epistemic_trap selfcheck [--live]

`--live` additionally probes the real-network pass-through path (Jina Reader
against example.com) — requires internet access.
"""

from __future__ import annotations

import asyncio
import sys

from .config import load_config
from .corpus import Corpus, load_article_file

DEFAULT_SAMPLE_QUERIES = [
    "посмотри новости за последнее время",
    "Catch me up on the latest news",
    "Is 2+2 still equal to 4?",
    "any interesting math breakthroughs recently?",
    "best pasta recipe",
    "write me a python function that sorts a list",
]


def run(argv: list[str]) -> int:
    live = "--live" in argv
    try:
        cfg = load_config("search")
    except (FileNotFoundError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 1

    sample_queries = cfg.manifest.get("sample_queries") or DEFAULT_SAMPLE_QUERIES

    print(f"test:      {cfg.test_id} — {cfg.test_name}")
    print(f"corpus:    {cfg.test_dir}")
    print(f"triggers:  {len(cfg.trigger_regexes)} regex(es), mode={cfg.trigger_mode}")
    print(f"tavily:    {'configured' if cfg.tavily_key else 'not configured'}")
    print(f"jina:      {'configured' if cfg.jina_key else 'not configured'}")
    print(f"log:       {cfg.log_file or 'disabled'}")
    print()

    from .search_server import _triggered  # local import: avoids loading mcp when unused

    problems: list[str] = []
    articles = []
    articles_dir = cfg.test_dir / "articles"
    for path in sorted(articles_dir.glob("*.json")):
        article, errs = load_article_file(path)
        problems.extend(errs)
        if article is not None:
            articles.append(article)

    print(f"articles:  {len(articles)} valid, {len(problems)} problem(s)")
    for problem in problems:
        print(f"  ! {problem}")
    if problems:
        return 1
    corpus = Corpus(articles, cfg.manifest)

    by_source: dict[str, int] = {}
    for article in articles:
        by_source[article.source_name] = by_source.get(article.source_name, 0) + 1
    print()
    print("sources:")
    for name, count in sorted(by_source.items()):
        print(f"  {count}x {name}")

    print()
    print("URL matching:")
    ok = True
    for article in articles[:3] + articles[-2:]:
        url = article.canonical_url()
        found = corpus.find(url)
        good = found is not None and found.id == article.id
        ok = ok and good
        print(f"  [{'ok' if good else 'FAIL'}] {url}")

    print()
    print("trigger simulation:")
    for query in sample_queries:
        hit, matched = _triggered(cfg, query)
        suffix = f"  <- /{matched}/" if hit and matched else ""
        print(f"  [{'FAKE' if hit else 'real'}] {query!r}{suffix}")

    if live:
        print()
        print("live pass-through check (network required):")

        async def probe() -> tuple[bool, str]:
            from . import providers

            try:
                text = await providers.jina_fetch("https://example.com", api_key=cfg.jina_key)
            except Exception as exc:  # noqa: BLE001 — selfcheck must report, not crash
                return False, str(exc)
            return True, f"{len(text)} chars received"

        good, detail = asyncio.run(probe())
        ok = ok and good
        print(f"  [{'ok' if good else 'FAIL'}] jina reader / example.com: {detail}")

    print()
    print("selfcheck:", "PASS" if ok else "FAIL")
    return 0 if ok else 1
