"""Tests for the contribution-calendar HTML parser."""

from __future__ import annotations

from datetime import date

from github_contributions.fetch import _parse_html

SAMPLE_HTML = """
<table>
  <td class="ContributionCalendar-day" data-date="2015-01-04"
      id="contribution-day-component-0-0" data-level="0"></td>
  <td class="ContributionCalendar-day" data-date="2015-01-05"
      id="contribution-day-component-1-0" data-level="2"></td>
  <td class="ContributionCalendar-day" data-date="2015-01-06"
      id="contribution-day-component-2-0" data-level="4"></td>
</table>
<tool-tip for="contribution-day-component-0-0" class="sr-only">
  No contributions on Sunday, January 4, 2015
</tool-tip>
<tool-tip for="contribution-day-component-1-0" class="sr-only">
  7 contributions on Monday, January 5, 2015
</tool-tip>
<tool-tip for="contribution-day-component-2-0" class="sr-only">
  1,024 contributions on Tuesday, January 6, 2015
</tool-tip>
"""


def test_parse_html_extracts_counts_by_date() -> None:
    counts = _parse_html(SAMPLE_HTML)
    assert counts[date(2015, 1, 4)] == 0
    assert counts[date(2015, 1, 5)] == 7
    assert counts[date(2015, 1, 6)] == 1024


def test_parse_html_day_without_tooltip_defaults_to_zero() -> None:
    html = '<td data-date="2020-06-01" id="contribution-day-component-3-3"></td>'
    counts = _parse_html(html)
    assert counts[date(2020, 6, 1)] == 0
