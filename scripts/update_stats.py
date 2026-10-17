#!/usr/bin/env python3
"""Render a GitHub profile stats SVG from GitHub's API. No external packages.

The resulting SVG only publishes aggregate counts. Private repository titles,
URLs, PR subjects, and identifiers are never requested or printed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USERNAME = os.environ.get("PROFILE_USERNAME", "PunishedK")
# A repo-scoped GITHUB_TOKEN cannot read other private repos. An optional PAT
# grants only the access the PAT owner configured.
PRIVATE_TOKEN = os.environ.get("PROFILE_STATS_TOKEN", "")
TOKEN = PRIVATE_TOKEN or os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "metrics.svg"


def github_get(path: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PunishedK-profile-stats",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        # Don't disclose the token or replace truthful historical stats with 0.
        raise RuntimeError(f"GitHub API HTTP {error.code} requesting {path.split('?')[0]}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError("Could not retrieve GitHub metrics; keeping existing SVG") from error


def search_count(query: str) -> int:
    params = urlencode({"q": query, "per_page": 1})
    data = github_get(f"/search/issues?{params}")
    if data.get("incomplete_results"):
        raise RuntimeError("GitHub search returned incomplete results; preserving previous metrics")
    return int(data["total_count"])


def read_metrics() -> tuple[int, int, int]:
    # Search counts PRs across all repos readable by the token, including
    # selected private repos with an appropriately permissioned PAT.
    opened = search_count(f"is:pr author:{USERNAME}")
    merged = search_count(f"is:pr author:{USERNAME} is:merged")
    public_repos = int(github_get(f"/users/{USERNAME}")["public_repos"])
    if merged > opened:
        raise RuntimeError("Inconsistent API results; preserving previous metrics")
    return opened, merged, public_repos


def render_svg(opened: str, merged: str, repos: str, scope: str) -> str:
    values = [escape(str(v)) for v in (opened, merged, repos)]
    labels = ["PULL REQUESTS", "MERGED PRS", "PUBLIC REPOS"]
    x_positions = [48, 444, 840]
    cards = []
    for x, value, label in zip(x_positions, values, labels):
        cards.append(f'''
          <rect x="{x}" y="56" width="360" height="140" rx="16" fill="#111c29" stroke="#2b4052"/>
          <rect x="{x + 22}" y="80" width="27" height="3" rx="1.5" fill="#71ded1"/>
          <text x="{x + 23}" y="141" font-family="Arial, Helvetica, sans-serif" font-size="50" font-weight="700" fill="#eff7fb">{value}</text>
          <text x="{x + 23}" y="174" font-family="Arial, Helvetica, sans-serif" font-size="13" letter-spacing="1.5" fill="#90aec0">{label}</text>''')
    # scope is authored locally, not scraped from GitHub content.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1248" height="242" viewBox="0 0 1248 242" role="img" aria-labelledby="title desc">
      <title id="title">PunishedK GitHub metrics</title>
      <desc id="desc">{values[0]} pull requests, {values[1]} merged pull requests, {values[2]} public repositories. {escape(scope)}.</desc>
      <rect x="0.5" y="0.5" width="1247" height="241" rx="20" fill="#0b131e" stroke="#223449"/>
      <text x="48" y="31" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="700" letter-spacing="2.2" fill="#b9d5df">GITHUB / LIVE METRICS</text>
      <text x="1198" y="31" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#829fb4">{escape(scope)}</text>
      {''.join(cards)}
      <text x="48" y="221" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#819bad">Source: GitHub API · Values change only when GitHub data changes</text>
    </svg>
'''


def main() -> None:
    opened, merged, repos = read_metrics()
    scope = "TOKEN-VISIBLE PRS" if PRIVATE_TOKEN else "PUBLIC / REPO-SCOPED PRS"
    new_data = render_svg(str(opened), str(merged), str(repos), scope)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == new_data:
        print("No changes to metrics. No commit necessary.")
        return
    OUTPUT.write_text(new_data, encoding="utf-8")
    print(f"Updated metrics SVG (opened={opened}, merged={merged}, public_repos={repos}, scope={scope})")


if __name__ == "__main__":
    main()
