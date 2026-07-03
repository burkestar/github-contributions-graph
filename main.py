"""Generate a GitHub contributions heatmap PNG for a user.

Usage:
    uv run python main.py [username] [start_year] [end_year]
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from github_contributions.fetch import fetch_range
from github_contributions.plot import render

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

DEFAULT_USER = "burkestar"
DEFAULT_START = 2014
DEFAULT_END = 2026


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    start = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_START
    end = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_END

    root = Path(__file__).parent
    cache_dir = root / "data"
    out_path = root / "output" / f"{user}-contributions-{start}-{end}.png"

    data = fetch_range(user, start, end, cache_dir)
    render(data, user, out_path)
    logging.info("wrote %s", out_path)


if __name__ == "__main__":
    main()
