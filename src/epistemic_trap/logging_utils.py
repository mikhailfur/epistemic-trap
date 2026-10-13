"""JSONL event logging: every tool call is recorded for experiment analysis.

The log is the researcher's primary data source (which queries triggered,
which synthetic ids were served, whether fetches passed through to the real
web). Logging failures are swallowed: instrumentation must never break the
harness or tip off the agent under test.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import TrapConfig


def log_event(cfg: TrapConfig, **fields: object) -> None:
    if cfg.log_file is None:
        return
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": cfg.mode,
        "test": cfg.test_id,
        **fields,
    }
    try:
        cfg.log_file.parent.mkdir(parents=True, exist_ok=True)
        with cfg.log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
