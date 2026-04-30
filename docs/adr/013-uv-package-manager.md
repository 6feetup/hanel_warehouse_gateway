# ADR-013 — uv as official package manager

**Status:** Accepted

## Context

The project previously documented `pip install -e ".[dev]"` as the standard installation command. While `pip` works correctly with the `pyproject.toml` + hatchling setup, `uv` offers significant advantages for development workflows: faster dependency resolution, deterministic lock files, and integrated virtual environment management.

The `pyproject.toml` build backend (hatchling) is fully compatible with `uv` without modification.

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| Keep `pip` | No change required, universally available | Slower, no lock file, no integrated venv management |
| Adopt `uv` | Fast, lock file for reproducibility, single tool for venv + install + run | Requires `uv` to be installed separately |
| Add `poetry` | Lock file, venv management | Requires rewriting `pyproject.toml`, heavier tooling |

## Decision

We adopt **`uv`** as the official package manager for development.

- `uv sync` replaces `pip install -e ".[dev]"` for environment setup
- `uv sync --no-dev` replaces `pip install -e .` for production-only installs
- `uv run <command>` is the canonical way to invoke tools (`pytest`, `mypy`, `ruff`)
- `uv.lock` is committed to the repository for reproducible development environments
- `.python-version` pins the minimum Python version (`3.10`) for `uv` to use

Dev dependencies are moved from `[project.optional-dependencies]` to `[dependency-groups]` (PEP 735): `uv` installs all dependency groups by default with `uv sync`, eliminating the need for `--extra dev`.

## Consequences

- Developers must install `uv` before working on the project (`brew install uv` or `pip install uv`)
- `uv.lock` must be updated when dependencies change (`uv lock` or automatically via `uv sync`)
- CI/CD pipelines must install `uv` before running setup steps
- The `mock_server/` Dockerfile retains `pip` — it is a standalone Flask container with no relation to this module's development workflow
