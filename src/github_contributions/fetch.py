"""Fetch daily GitHub contribution counts for a user.

Parses GitHub's own public contribution calendar HTML
(``github.com/users/<user>/contributions``), which exposes exact per-day
counts via the accessibility tool-tips. Results are cached on disk so the
network is only hit once per (user, year).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

CONTRIB_URL = "https://github.com/users/{user}/contributions"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

# <td ... data-date="2015-01-05" ... id="contribution-day-component-0-5" ...>
_TD_RE = re.compile(r"<td\b[^>]*>", re.IGNORECASE)
_DATE_RE = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"')
_ID_RE = re.compile(r'id="(contribution-day-component-\d+-\d+)"')
# <tool-tip ... for="contribution-day-component-0-5" ...>1 contribution on ...</tool-tip>
_TOOLTIP_RE = re.compile(
    r'<tool-tip\b[^>]*\bfor="(contribution-day-component-\d+-\d+)"[^>]*>(.*?)</tool-tip>',
    re.IGNORECASE | re.DOTALL,
)
_COUNT_RE = re.compile(r"^([\d,]+)\s+contribution")


def _parse_html(html: str) -> dict[date, int]:
    """Extract {date: count} from a contributions calendar HTML fragment."""
    # cell id -> exact count, from the tool-tips.
    id_to_count: dict[str, int] = {}
    for cell_id, text in _TOOLTIP_RE.findall(html):
        text = text.strip()
        match = _COUNT_RE.match(text)
        id_to_count[cell_id] = int(match.group(1).replace(",", "")) if match else 0

    # cell id -> date, from the day <td> tags.
    counts: dict[date, int] = {}
    for tag in _TD_RE.findall(html):
        date_m = _DATE_RE.search(tag)
        id_m = _ID_RE.search(tag)
        if not date_m or not id_m:
            continue
        day = date.fromisoformat(date_m.group(1))
        counts[day] = id_to_count.get(id_m.group(1), 0)
    return counts


def fetch_year(user: str, year: int, cache_dir: Path) -> dict[date, int]:
    """Return {date: count} for every day of ``year`` for ``user``."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{user}-{year}.json"

    if cache_file.exists():
        logger.info("cache hit %s", cache_file.name)
        raw = json.loads(cache_file.read_text())
        return {date.fromisoformat(d): c for d, c in raw.items()}

    logger.info("fetching %s %s", user, year)
    resp = httpx.get(
        CONTRIB_URL.format(user=user),
        params={"from": f"{year}-01-01", "to": f"{year}-12-31"},
        headers={"User-Agent": USER_AGENT, "X-Requested-With": "XMLHttpRequest"},
        timeout=30.0,
        follow_redirects=True,
    )
    resp.raise_for_status()

    parsed = _parse_html(resp.text)
    counts = {d: c for d, c in parsed.items() if d.year == year}
    if not counts:
        raise RuntimeError(f"no contribution data parsed for {user} {year}")

    cache_file.write_text(json.dumps({d.isoformat(): c for d, c in counts.items()}))
    return counts


def fetch_range(
    user: str, start_year: int, end_year: int, cache_dir: Path
) -> dict[int, dict[date, int]]:
    """Return {year: {date: count}} for every year in the inclusive range."""
    return {
        year: fetch_year(user, year, cache_dir)
        for year in range(start_year, end_year + 1)
    }
