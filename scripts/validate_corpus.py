#!/usr/bin/env python3
"""Validate article JSON files or whole article directories.

Usage:
  python scripts/validate_corpus.py FILE.json [FILE.json ...]
  python scripts/validate_corpus.py corpus/test_a_numeracy/articles/

Exit code 0 when every file passes, 1 otherwise. Used both by contributors
and by the CI workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epistemic_trap.corpus import load_article_file  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    targets: list[Path] = []
    for arg in argv:
        path = Path(arg)
        if path.is_dir():
            targets.extend(sorted(path.glob("*.json")))
        else:
            targets.append(path)
    failures = 0
    for path in targets:
        _, errors = load_article_file(path)
        if errors:
            failures += 1
            for error in errors:
                print(f"FAIL {error}")
        else:
            print(f"ok   {path}")
    print(f"\n{len(targets) - failures}/{len(targets)} files valid")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
