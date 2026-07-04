# github-contributions

Render a multi-year GitHub contributions heatmap to a PNG, using GitHub's own
green color scale, normalized to the full range of daily contribution counts.

Daily counts are read from GitHub's public contribution calendar
(`github.com/users/<user>/contributions`) and cached under `data/`.

> [!WARNING]  
> This repository was vibecoded using Claude Code and should be considered ALPHA quality.
> No test coverage, no agent harness, no automated tests or guardrails.
> Github contributions are scraped from the user's public page and does not use any
> API credentials, so there is no risk of stolen credentials. Caveat emptor!

## Usage

```bash
uv run python main.py                      # burkestar, 2014–2026 (defaults)
uv run python main.py <username>           # a different user
uv run python main.py <username> 2018 2024 # a custom inclusive year range
```

The PNG is written to `output/<user>-contributions-<start>-<end>.png`.

## Development

```bash
uv run ruff format .
uv run ruff check . --fix
uv run mypy src/
uv run pytest
```
