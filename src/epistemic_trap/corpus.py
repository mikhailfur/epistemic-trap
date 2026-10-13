"""Loading, validation and URL-matching for synthetic article corpora."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,39}$")

# Giveaway words that must never appear in article ids (stealth requirement).
ID_FORBIDDEN = ("fake", "synthetic", "hoax", "satire", "trap", "test", "fiction")

# Entry kinds: a full news article, an outage/status page (Downdetector,
# status.openai.com), an error/defacement page (a site that is "down"), or a
# social-media thread page. Articles keep the strictest rules.
KINDS = ("article", "status", "error_page", "social")

REQUIRED_KEYS: dict[str, type] = {
    "id": str,
    "source_name": str,
    "source_domain": str,
    "path_template": str,
    "title": str,
    "snippet": str,
    "authors": list,
    "hours_ago": int,
    "category": str,
    "body_markdown": str,
}


@dataclass
class Article:
    id: str
    source_name: str
    source_domain: str
    path_template: str
    title: str
    snippet: str
    authors: list[str]
    hours_ago: int
    category: str
    body_markdown: str
    kind: str = "article"
    host_match: bool = False

    @property
    def uses_id_in_path(self) -> bool:
        return "{id}" in self.path_template

    def canonical_url(self) -> str:
        return f"https://{self.source_domain}{self.path_template.format(id=self.id)}"

    def published_at(self, now: datetime | None = None) -> datetime:
        now = now or datetime.now(timezone.utc)
        return now - timedelta(hours=self.hours_ago)

    def published_iso(self, now: datetime | None = None) -> str:
        return self.published_at(now).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_article(data: object, path: Path) -> list[str]:
    """Return human-readable problems; an empty list means the file is valid."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: top level must be a JSON object"]
    for key, expected in REQUIRED_KEYS.items():
        if key not in data:
            errors.append(f"{path}: missing required key '{key}'")
        elif not isinstance(data[key], expected):
            errors.append(
                f"{path}: '{key}' must be {expected.__name__}, got {type(data[key]).__name__}"
            )
    if errors:
        return errors

    kind = str(data.get("kind", "article"))
    if kind not in KINDS:
        errors.append(f"{path}: kind must be one of {KINDS}, got '{kind}'")
        kind = "article"
    host_match = bool(data.get("host_match", False))

    if not ID_RE.match(data["id"]):
        errors.append(f"{path}: id '{data['id']}' must match {ID_RE.pattern}")
    lowered = data["id"].lower()
    if any(word in lowered for word in ID_FORBIDDEN):
        errors.append(f"{path}: id must not contain giveaway words {ID_FORBIDDEN}")
    if not data["source_domain"].strip():
        errors.append(f"{path}: source_domain is empty")
    template = data["path_template"]
    if not template.startswith("/"):
        errors.append(f"{path}: path_template must start with '/'")
    try:
        template.format(id=data["id"])
    except (KeyError, IndexError, ValueError) as exc:
        errors.append(f"{path}: path_template format failed: {exc}")
    if host_match and kind not in ("error_page", "status"):
        errors.append(f"{path}: host_match is only allowed for kind 'status' or 'error_page'")
    if not data["title"].strip():
        errors.append(f"{path}: title is empty")
    snippet_words = len(data["snippet"].split())
    snippet_min = 12 if kind == "article" else 8
    if not snippet_min <= snippet_words <= 90:
        errors.append(f"{path}: snippet should be {snippet_min}-90 words, got {snippet_words}")
    if kind == "article" and not data["authors"]:
        errors.append(f"{path}: authors must not be empty (use e.g. [\"Staff Reporter\"])")
    if kind == "social" and not data["authors"]:
        errors.append(f"{path}: social entries need an author (the account name)")
    if not 1 <= int(data["hours_ago"]) <= 336:
        errors.append(f"{path}: hours_ago must be in 1..336")
    body = data["body_markdown"].strip()
    min_chars = {"article": 2500, "status": 1000, "error_page": 800, "social": 800}[kind]
    if len(body) < min_chars:
        errors.append(f"{path}: body_markdown too short ({len(body)} chars, want >= {min_chars})")
    if body.startswith("# "):
        errors.append(f"{path}: body_markdown must not start with an H1 (renderer adds one)")
    return errors


def load_article_file(path: Path) -> tuple[Article | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    except OSError as exc:
        return None, [f"{path}: unreadable: {exc}"]
    errors = validate_article(data, path)
    if errors:
        return None, errors
    article = Article(
        id=data["id"],
        source_name=data["source_name"],
        source_domain=data["source_domain"].lower(),
        path_template=data["path_template"],
        title=data["title"],
        snippet=data["snippet"],
        authors=[str(a) for a in data["authors"]],
        hours_ago=int(data["hours_ago"]),
        category=data["category"],
        body_markdown=data["body_markdown"],
        kind=str(data.get("kind", "article")),
        host_match=bool(data.get("host_match", False)),
    )
    return article, []


class Corpus:
    """A validated set of articles for one test."""

    def __init__(self, articles: list[Article], manifest: dict):
        self.articles = articles
        self.manifest = manifest

    @classmethod
    def load(cls, test_dir: Path) -> "Corpus":
        manifest_path = test_dir / "test.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        articles_dir = test_dir / "articles"
        if not articles_dir.is_dir():
            raise FileNotFoundError(f"Articles directory not found: {articles_dir}")
        articles: list[Article] = []
        problems: list[str] = []
        seen: dict[str, Path] = {}
        for path in sorted(articles_dir.glob("*.json")):
            article, errs = load_article_file(path)
            problems.extend(errs)
            if article is None:
                continue
            if article.id in seen:
                problems.append(f"{path}: duplicate id '{article.id}' (also {seen[article.id]})")
                continue
            seen[article.id] = path
            articles.append(article)
        if problems:
            raise ValueError("Corpus validation failed:\n" + "\n".join(problems))
        if not articles:
            raise ValueError(f"No valid articles found in {articles_dir}")
        return cls(articles, manifest)

    def find(self, url: str) -> Article | None:
        """Match a requested URL against the corpus.

        An article is served when the URL equals its canonical URL (host +
        path, ignoring scheme/query/fragment and a trailing slash), or — for
        articles whose path embeds `{id}` — when the unique article id occurs
        anywhere in the URL (caches, AMP mirrors, pagination suffixes, ...).
        `host_match` entries (a site that is "down") additionally serve every
        path on their domain.
        """
        try:
            parts = urlsplit(url.strip())
        except ValueError:
            return None
        host = (parts.netloc or "").lower()
        path = (parts.path or "").rstrip("/")
        clean = f"{host}{path}"
        for article in self.articles:
            canonical = (
                f"{article.source_domain}{article.path_template.format(id=article.id)}"
            ).rstrip("/")
            if clean == canonical:
                return article
        if host:
            for article in self.articles:
                if article.uses_id_in_path and article.id in f"{host}{path}".lower():
                    return article
        host_core = host[4:] if host.startswith("www.") else host
        if host_core:
            candidates = []
            for article in self.articles:
                if not article.host_match:
                    continue
                domain = article.source_domain
                domain = domain[4:] if domain.startswith("www.") else domain
                exact = host_core == domain
                subdomain = host_core.endswith("." + domain)
                if exact or subdomain:
                    candidates.append((0 if exact else 1, article))
            if candidates:
                # An exact host match (status.openai.com -> its own entry)
                # always wins over a subdomain match (-> the apex's entry).
                return min(candidates, key=lambda pair: pair[0])[1]
        return None
