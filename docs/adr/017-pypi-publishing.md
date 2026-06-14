# ADR-017 — Publishing to PyPI via Trusted Publishing

**Status:** Accepted

**Date:** 2026-06-14

## Context

The module was distributed only as GitHub Release artifacts (wheel + sdist built with
`uv build`). To let other Python projects depend on it with `pip install` / `uv add`,
it must be available on a package registry.

A registry was required for public, Python-native consumption. The relevant facts:

- The consumers are **Python** projects, so the artifact must be an importable Python
  package (a wheel/sdist), not an npm package.
- **PyPI** is the only public registry that hosts Python packages. GitHub Packages
  supports npm, Maven, NuGet, RubyGems and containers — **not** Python distributions.

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| Keep GitHub Release artifacts only | No registry account needed | Consumers must pin a Git/URL dependency; no `pip install <name>` |
| Public **PyPI** | Standard `pip install` / `uv add`; discoverable | Requires a PyPI account and publish credentials |
| GitHub Packages | Integrated with the repo | Does not host Python packages — not applicable |

## Decision

Publish the package to **public PyPI**, integrated into the existing release-please
workflow, using **Trusted Publishing (OIDC)** rather than a long-lived API token.

- A `publish-pypi` job is added to `.github/workflows/release-please.yml`, gated on
  `release_created == 'true'` like the other release jobs.
- The job runs in the `pypi` GitHub Environment with `id-token: write`, builds with
  `uv build`, and publishes via `pypa/gh-action-pypi-publish`.
- No `PYPI_API_TOKEN` secret is stored; PyPI verifies the workflow identity through OIDC.
- GitHub Release artifact upload (`build-artifacts`) is kept; PyPI and GitHub Releases
  coexist.

The source distribution is restricted via `[tool.hatch.build.targets.sdist]` to
`src/`, `README.md`, `CHANGELOG.md`, the license files (`LICENSE`, `LICENSE.GPL`) and
`pyproject.toml`. Development-only content
(`docs/`, `.claude/`, `.github/`, `tests/`, `docker-compose`, mock server) is excluded.
The wheel already contained only the `src/hanel_warehouse_gateway` package.

Versioning remains owned by release-please via `.release-please-manifest.json`; no
manual version bump is involved in publishing.

## Prerequisites (one-time, manual)

- Register a Trusted Publisher on pypi.org for the `hanel-warehouse-gateway` project,
  pointing at repo `6feetup/hanel_warehouse_gateway`, workflow `release-please.yml`,
  and environment `pypi`.
- Confirm the project name is available on PyPI.
- Licensing question — resolved in this change: the project previously declared
  `license = "Proprietary"`, which is incompatible with allowing anyone to use the
  package. It now adopts `LGPL-3.0-or-later`, with the LGPL text in `LICENSE` and the
  GPL v3 it incorporates in `LICENSE.GPL`. LGPL (rather than GPL) is chosen so that
  downstream Python projects can depend on the package without their own code becoming
  subject to copyleft, while modifications to this library itself remain copyleft.

## Consequences

- Each release automatically appears on PyPI; consumers install with
  `pip install hanel-warehouse-gateway` or `uv add hanel-warehouse-gateway`.
- No publish secret to rotate or leak.
- The `pypi` environment can carry protection rules (required reviewers) if desired.
- If the project name or license changes, this ADR and `pyproject.toml` must be updated.
