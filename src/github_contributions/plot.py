"""Render a multi-year GitHub-style contribution heatmap to PNG."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch

# GitHub's contribution palette. The lightest cell (#ebedf0) is reserved for
# days with zero contributions; the green ramp is used for everything > 0.
EMPTY_COLOR = "#ebedf0"
GREEN_RAMP = ["#9be9a8", "#40c463", "#30a14e", "#216e39"]

MONTH_LABELS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # row index (Sun=0 at top) -> label

CELL = 1.0  # logical cell pitch
PAD = 0.15  # gap between cells
RADIUS = 0.18  # rounded-corner radius


def _github_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("github-green", GREEN_RAMP)


def _week_index(day: date, year: int) -> int:
    """Column for ``day`` within its year grid (weeks since first Sunday)."""
    jan1 = date(year, 1, 1)
    # Sunday-on-or-before Jan 1 anchors column 0, matching GitHub's layout.
    anchor = jan1 - timedelta(days=(jan1.weekday() + 1) % 7)
    return (day - anchor).days // 7


def _weekday_row(day: date) -> int:
    """Row for ``day`` with Sunday at the top (0) and Saturday at the bottom (6)."""
    return (day.weekday() + 1) % 7


def _color(
    count: int, norm: Normalize, cmap: LinearSegmentedColormap
) -> str | tuple[float, ...]:
    if count <= 0:
        return EMPTY_COLOR
    return cmap(norm(count))


def render(
    data: dict[int, dict[date, int]],
    user: str,
    out_path: Path,
) -> Path:
    """Render ``{year: {date: count}}`` to a PNG heatmap at ``out_path``."""
    years = sorted(data)
    global_max = max(
        (c for counts in data.values() for c in counts.values()), default=0
    )
    # Normalize positive counts across their full range so color scales with
    # activity. Guard against a flat/empty history.
    norm = Normalize(vmin=1, vmax=max(global_max, 1))
    cmap = _github_cmap()

    # 53 possible week columns + a little room for the weekday labels on the left.
    weeks_wide = 53
    label_cols = 3.5
    row_height = 7 + 3.0  # 7 weekday rows + month labels + year title gutter

    fig_w = (weeks_wide + label_cols) * 0.16
    fig_h = len(years) * row_height * 0.16
    fig, axes = plt.subplots(len(years), 1, figsize=(fig_w, fig_h), squeeze=False)
    axes = axes[:, 0]

    for ax, year in zip(axes, years):
        counts = data[year]
        year_total = sum(counts.values())
        month_first_col: dict[int, int] = {}

        for day, count in counts.items():
            col = _week_index(day, year)
            row = _weekday_row(day)
            # y grows downward (Sun at top) -> invert with (6 - row)
            x = label_cols + col * CELL
            y = (6 - row) * CELL
            box = FancyBboxPatch(
                (x + PAD / 2, y + PAD / 2),
                CELL - PAD,
                CELL - PAD,
                boxstyle=f"round,pad=0,rounding_size={RADIUS}",
                linewidth=0,
                facecolor=_color(count, norm, cmap),
            )
            ax.add_patch(box)

            month = day.month
            if month not in month_first_col and day.day <= 7:
                month_first_col[month] = col

        # Month labels along the top.
        for month, col in month_first_col.items():
            ax.text(
                label_cols + col * CELL,
                7 * CELL + 0.35,
                MONTH_LABELS[month - 1],
                fontsize=6.5,
                ha="left",
                va="bottom",
                color="#57606a",
            )

        # Weekday labels down the left.
        for row, label in WEEKDAY_LABELS.items():
            ax.text(
                label_cols - 0.4,
                (6 - row) * CELL + CELL / 2,
                label,
                fontsize=6.5,
                ha="right",
                va="center",
                color="#57606a",
            )

        # Year + total, top-left.
        ax.text(
            0,
            7 * CELL + 1.4,
            f"{year}",
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="bottom",
            color="#24292f",
        )
        ax.text(
            label_cols + 0.2,
            7 * CELL + 1.55,
            f"{year_total:,} contributions",
            fontsize=7,
            ha="left",
            va="bottom",
            color="#57606a",
        )

        ax.set_xlim(-0.2, label_cols + weeks_wide * CELL)
        ax.set_ylim(-0.4, 7 * CELL + 2.6)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.suptitle(
        f"@{user} — GitHub contributions {years[0]}–{years[-1]}",
        fontsize=15,
        fontweight="bold",
        y=0.995,
    )

    # Legend: Less -> More swatches, bottom-right of the figure.
    _add_legend(fig, cmap)

    fig.tight_layout(rect=(0, 0.0, 1, 0.985))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def _add_legend(fig, cmap: LinearSegmentedColormap) -> None:
    """Add a 'Less -> More' swatch strip in figure coordinates."""
    swatches = [EMPTY_COLOR] + [cmap(t) for t in (0.15, 0.4, 0.7, 1.0)]
    n = len(swatches)
    sw = 0.012
    gap = 0.004
    x0 = 0.72
    y0 = 0.006
    fig.text(
        x0 - 0.01,
        y0 + sw / 2,
        "Less",
        fontsize=8,
        ha="right",
        va="center",
        color="#57606a",
    )
    for i, color in enumerate(swatches):
        fig.patches.append(
            plt.Rectangle(
                (x0 + i * (sw + gap), y0),
                sw,
                sw,
                transform=fig.transFigure,
                facecolor=color,
                edgecolor="none",
            )
        )
    fig.text(
        x0 + n * (sw + gap) + 0.005,
        y0 + sw / 2,
        "More",
        fontsize=8,
        ha="left",
        va="center",
        color="#57606a",
    )
