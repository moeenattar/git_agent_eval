#!/usr/bin/env python3
"""Fetch raw public GitHub issues without introducing a runtime dependency."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _request(url: str, token: str | None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-triage-eval-dataset-builder",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response), dict(response.headers)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned {exc.code}: {detail}") from exc


def _next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        url_part, *parameters = part.split(";")
        if any('rel="next"' in parameter for parameter in parameters):
            return url_part.strip()[1:-1]
    return None


def fetch(repo: str, state: str, limit: int, token: str | None) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"state": state, "per_page": min(100, limit)})
    url: str | None = f"https://api.github.com/repos/{repo}/issues?{query}"
    issues: list[dict[str, Any]] = []
    while url and len(issues) < limit:
        page, headers = _request(url, token)
        for item in page:
            if "pull_request" in item:
                continue
            issues.append(
                {
                    "id": f"{repo.replace('/', '-')}-{item['number']}",
                    "repo": repo,
                    "number": item["number"],
                    "url": item["html_url"],
                    "state": item["state"],
                    "title": item["title"],
                    "body": item.get("body") or "",
                    "labels": [label["name"] for label in item.get("labels", [])],
                    "created_at": item["created_at"],
                    "closed_at": item.get("closed_at"),
                    "fetched_at_unix": int(time.time()),
                }
            )
            if len(issues) >= limit:
                break
        url = _next_link(headers.get("Link"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="python/pythondotorg")
    parser.add_argument("--state", choices=["open", "closed", "all"], default="all")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")

    issues = fetch(args.repo, args.state, args.limit, os.getenv("GITHUB_TOKEN"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for issue in issues:
            handle.write(json.dumps(issue, ensure_ascii=False) + "\n")
    print(f"Wrote {len(issues)} issues to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
