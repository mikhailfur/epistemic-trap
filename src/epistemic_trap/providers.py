"""Upstream providers used for pass-through of *real* web content.

The harness only ever calls these with the researcher's own API keys, for
queries that do not match the test's trigger regexes (search) or for URLs
outside the synthetic corpus (fetch).
"""

from __future__ import annotations

import httpx

TAVILY_ENDPOINT = "https://api.tavily.com/search"
JINA_READER = "https://r.jina.ai/"


class ProviderError(RuntimeError):
    pass


async def tavily_search(
    query: str,
    *,
    api_key: str,
    max_results: int = 8,
    search_depth: str = "basic",
    timeout: float = 15.0,
) -> list[dict]:
    payload = {
        "query": query,
        "max_results": max(1, min(int(max_results), 20)),
        "search_depth": search_depth if search_depth in ("basic", "advanced") else "basic",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.post(TAVILY_ENDPOINT, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise ProviderError(f"tavily request failed: {exc}") from exc
    if response.status_code != 200:
        raise ProviderError(f"tavily returned HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ProviderError("tavily returned a non-JSON body") from exc
    results = []
    for item in data.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score"),
                "published_date": item.get("published_date"),
            }
        )
    return results


async def jina_fetch(url: str, *, api_key: str | None = None, timeout: float = 25.0) -> str:
    """Read a real page through the Jina Reader and return markdown text.

    Works without an API key at a low rate limit; pass `JINA_API_KEY` for
    higher limits.
    """
    headers = {"Accept": "text/plain", "X-Return-Format": "markdown"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(JINA_READER + url, headers=headers)
    except httpx.HTTPError as exc:
        raise ProviderError(f"jina reader request failed: {exc}") from exc
    if response.status_code != 200:
        raise ProviderError(f"jina reader returned HTTP {response.status_code} for {url}")
    return response.text
