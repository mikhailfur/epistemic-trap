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
    if not data["title"].strip():
        errors.append(f"{path}: title is empty")
    snippet_words = len(data["snippet"].split())
    if not 12 <= snippet_words <= 90:
        errors.append(f"{path}: snippet should be 12-90 words, got {snippet_words}")
    if not data["authors"]:
        errors.append(f"{path}: authors must not be empty (use e.g. [\"Staff Reporter\"])")
    if not 1 <= int(data["hours_ago"]) <= 336:
        errors.append(f"{path}: hours_ago must be in 1..336")
    body = data["body_markdown"].strip()
    if len(body) < 2500:
        errors.append(f"{path}: body_markdown too short ({len(body)} chars, want >= 2500)")
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
        return None
