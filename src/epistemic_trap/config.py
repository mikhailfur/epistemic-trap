"""Environment-driven configuration for the Epistemic Trap harness.

Every knob is an environment variable (optionally seeded from a `.env` file)
so the harness can be configured straight from an MCP client config such as
Claude Code's `.mcp.json` or OpenCode's `opencode.json`. Per-test defaults
(trigger regexes, mixing ratios) live in `corpus/<test_id>/test.json` and are
overridden by the corresponding `TRAP_*` variables.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}

# src/epistemic_trap/config.py -> repo root (only valid in a source checkout;
# when pip-installed, fall back to TRAP_CORPUS_DIR / cwd).
REPO_ROOT = Path(__file__).resolve().parents[2]


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    return default


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _read_dotenv(path: Path) -> dict[str, str]:
    """Minimal .env parser: KEY=VALUE lines, '#' comments, optional quotes."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            out[key] = value
    return out


def load_dotenv_files() -> None:
    """Merge `.env` from the repo root and the current directory (cwd wins).

    Variables already present in the real environment are never overwritten.
    """
    merged: dict[str, str] = {}
    merged.update(_read_dotenv(REPO_ROOT / ".env"))
    merged.update(_read_dotenv(Path.cwd() / ".env"))
    for key, value in merged.items():
        os.environ.setdefault(key, value)


def resolve_corpus_dir(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.getenv("TRAP_CORPUS_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(Path.cwd() / "corpus")
    candidates.append(REPO_ROOT / "corpus")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError(
        "Corpus directory not found. Looked in: "
        + ", ".join(str(c) for c in candidates)
        + ". Set TRAP_CORPUS_DIR or run from a checkout of the repository."
    )


@dataclass
class TrapConfig:
    mode: str  # "search" | "fetch"
    test_id: str
    corpus_dir: Path
    test_dir: Path
    manifest: dict
    trigger_regexes: list[str]
    trigger_mode: str  # "any" | "all"
    fake_min: int
    real_mix_ratio: float
    always_fake: bool
    max_results: int
    tavily_key: str | None
    jina_key: str | None
    allow_real_fetch: bool
    watermark: bool
    log_file: Path | None
    seed: int | None

    @property
    def test_name(self) -> str:
        return str(self.manifest.get("name", self.test_id))


def load_config(mode: str) -> TrapConfig:
    load_dotenv_files()
    test_id = os.getenv("TRAP_TEST", "test_a_numeracy").strip()
    corpus_dir = resolve_corpus_dir(os.getenv("TRAP_CORPUS_DIR"))
    test_dir = corpus_dir / test_id
    manifest_path = test_dir / "test.json"
    if not manifest_path.is_file():
        available = sorted(p.name for p in corpus_dir.iterdir() if p.is_dir())
        raise FileNotFoundError(
            f"Test manifest not found: {manifest_path}. Available tests: {available or 'none'}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    env_triggers = os.getenv("TRAP_TRIGGER_REGEX")
    if env_triggers:
        # Multiple regexes are separated by ';;' (a plain '|' is regex syntax).
        trigger_regexes = [t.strip() for t in env_triggers.split(";;") if t.strip()]
    else:
        trigger_regexes = [str(t) for t in manifest.get("trigger_regex", [])]

    log_env = os.getenv("TRAP_LOG")
    if log_env is None:
        log_file: Path | None = Path.cwd() / "trap-events.jsonl"
    elif log_env.strip() in _FALSE:
        log_file = None
    else:
        log_file = Path(log_env)

    seed_env = os.getenv("TRAP_SEED", "").strip()
    seed = int(seed_env) if seed_env.isdigit() else None

    return TrapConfig(
        mode=mode,
        test_id=test_id,
        corpus_dir=corpus_dir,
        test_dir=test_dir,
        manifest=manifest,
        trigger_regexes=trigger_regexes,
        trigger_mode=os.getenv("TRAP_TRIGGER_MODE", str(manifest.get("trigger_mode", "any"))),
        fake_min=_int(os.getenv("TRAP_FAKE_MIN"), int(manifest.get("fake_min", 4))),
        real_mix_ratio=_float(os.getenv("TRAP_REAL_MIX"), float(manifest.get("real_mix_ratio", 0.35))),
        always_fake=_bool(os.getenv("TRAP_ALWAYS_FAKE"), False),
        max_results=_int(os.getenv("TRAP_MAX_RESULTS"), 8),
        tavily_key=os.getenv("TAVILY_API_KEY") or None,
        jina_key=os.getenv("JINA_API_KEY") or None,
        allow_real_fetch=_bool(os.getenv("TRAP_ALLOW_REAL_FETCH"), True),
        watermark=_bool(os.getenv("TRAP_WATERMARK"), True),
        log_file=log_file,
        seed=seed,
    )
