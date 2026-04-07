"""Brave Search API wrapper for riddle originality evidence."""

from __future__ import annotations

import requests


def search_riddle_evidence(
    answer: str,
    api_key: str,
    max_snippets: int = 5,
    timeout: float = 5.0,
) -> dict | None:
    """Search Brave for '{answer} なぞなぞ' and return hit count + snippets.

    Returns:
        {"hit_count": int, "snippets": list[str]} on success, None on error.
    """
    if not api_key:
        return None

    query = f"{answer} なぞなぞ"

    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": api_key},
            params={"q": query, "count": max_snippets, "search_lang": "jp"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception:
        return None

    data = resp.json()
    web = data.get("web", {})
    hit_count = web.get("totalEstimatedMatches", 0)
    results = web.get("results", [])

    snippets = []
    for r in results[:max_snippets]:
        title = r.get("title", "")
        desc = r.get("description", "")
        url = r.get("url", "")
        snippets.append(f"{title} — {desc} ({url})")

    return {"hit_count": hit_count, "snippets": snippets}
