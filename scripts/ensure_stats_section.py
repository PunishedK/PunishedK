#!/usr/bin/env python3
"""Insert an idempotent stats section without replacing the existing profile."""

from __future__ import annotations

import re
import sys
from pathlib import Path

START = "<!-- PROFILE_STATS_START -->"
END = "<!-- PROFILE_STATS_END -->"
BLOCK = """<!-- PROFILE_STATS_START -->
### GitHub activity

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/profile-stats-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/profile-stats-light.svg">
  <img src="./assets/profile-stats-light.svg" alt="Real GitHub activity, automatically refreshed" width="100%">
</picture>
<!-- PROFILE_STATS_END -->"""


def update_readme(text: str) -> str:
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError("Malformed GitHub statistics section markers")
        pattern = re.escape(START) + r".*?" + re.escape(END)
        return re.sub(pattern, lambda _: BLOCK, text, count=1, flags=re.S)

    contributions_header = re.search(r"(?m)^#{2,4}\s+Contributions\s*$", text)
    if contributions_header:
        return text[:contributions_header.start()] + BLOCK + "\n\n" + text[contributions_header.start():]
    return text.rstrip() + "\n\n" + BLOCK + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "README.md"
    current = path.read_text(encoding="utf-8")
    updated = update_readme(current)
    if updated != current:
        path.write_text(updated, encoding="utf-8")
        print("Inserted/updated statistics in README (existing content preserved)")
    else:
        print("README statistics block unchanged")


if __name__ == "__main__":
    main()
