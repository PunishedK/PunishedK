#!/usr/bin/env python3
"""Build deterministic GitHub activity SVGs. Never invent contributions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""

THEMES = {
    "dark": {
        "background": "#0d1117", "panel": "#151b23", "border": "#30363d",
        "title": "#f0f6fc", "muted": "#919eac", "accent": "#60dcc5",
    },
    "light": {
        "background": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de",
        "title": "#1f2328", "muted": "#59636e", "accent": "#087f8c",
    },
}


def request_json(url: str, token: str, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PunishedK-profile-stats",
        "Authorization": f"Bearer {token}",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, headers=headers, data=data, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=25) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub API request failed: {url} ({exc})") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Invalid GitHub API response")
    return result


def read_live_stats(username: str, token: str) -> tuple[int, int, int, int]:
    if not token:
        raise RuntimeError("GITHUB_TOKEN is missing; refusing to display invented data")
    graph = request_json(
        "https://api.github.com/graphql", token,
        {"query": GRAPHQL_QUERY, "variables": {"login": username}},
    )
    if graph.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {graph['errors']}")
    user = (graph.get("data") or {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user @{username} was not returned")
    activity = user["contributionsCollection"]
    profile = request_json(f"https://api.github.com/users/{username}", token)
    values = (
        activity["contributionCalendar"]["totalContributions"],
        activity["totalCommitContributions"],
        activity["totalPullRequestContributions"],
        profile["public_repos"],
    )
    if any(type(value) is not int or value < 0 for value in values):
        raise RuntimeError("Invalid GitHub activity count")
    return values


def render_svg(values: tuple[int, int, int, int], theme: str) -> str:
    palette = THEMES[theme]
    labels = ("CONTRIBUTIONS / 12M", "COMMITS / 12M", "PULL REQUESTS / 12M", "PUBLIC REPOSITORIES")
    cards = []
    for index, (label, value) in enumerate(zip(labels, values)):
        x = 16 + index * 216
        cards.append(f"""
  <g transform="translate({x} 46)">
    <rect width="200" height="106" rx="12" fill="{palette['panel']}" stroke="{palette['border']}"/>
    <rect x="14" y="15" width="23" height="3" rx="1.5" fill="{palette['accent']}"/>
    <text x="14" y="50" fill="{palette['title']}" font-size="30" font-weight="700" font-family="DejaVu Sans,Arial,sans-serif">{value:,}</text>
    <text x="14" y="82" fill="{palette['muted']}" font-size="11" font-weight="600" letter-spacing="0.6" font-family="DejaVu Sans,Arial,sans-serif">{label}</text>
  </g>""")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="896" height="169" viewBox="0 0 896 169" role="img" aria-label="Real GitHub activity stats">
  <rect width="896" height="169" rx="14" fill="{palette['background']}"/>
  <text x="17" y="28" fill="{palette['title']}" font-size="14" font-weight="700" font-family="DejaVu Sans,Arial,sans-serif">GITHUB ACTIVITY</text>
  <text x="879" y="28" text-anchor="end" fill="{palette['muted']}" font-size="11" font-family="DejaVu Sans,Arial,sans-serif">GitHub API data</text>
{''.join(cards)}
</svg>
"""
    ET.fromstring(svg)
    return svg


def write_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    username = os.environ.get("PROFILE_USERNAME", "PunishedK")
    token = os.environ.get("GITHUB_TOKEN", "")
    values = read_live_stats(username, token)
    updated = []
    for theme in ("light", "dark"):
        path = root / "assets" / f"profile-stats-{theme}.svg"
        if write_if_changed(path, render_svg(values, theme)):
            updated.append(path.name)
    print("GitHub API statistics:", values)
    print("Updated: " + ", ".join(updated) if updated else "No values changed")


if __name__ == "__main__":
    main()
