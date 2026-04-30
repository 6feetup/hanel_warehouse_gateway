# ADR-014 — Documentation toolchain

**Status:** Accepted

## Context

The module needs structured technical documentation for integrators that covers:
- Public API reference (classes, methods, dataclasses, exceptions)
- Architecture Decision Records already written in Markdown
- CLI tool and end-to-end testing guide

Docstrings across all public modules are already of high quality. The goal is to render them into a navigable, searchable documentation site without duplicating content.

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| Custom script (stdlib `inspect`) | No new dependencies | Reinvents rendering logic; harder to maintain |
| **Sphinx + autodoc** | Python standard, very powerful | Heavy configuration, RST syntax, steep setup |
| **MkDocs + mkdocstrings** | Markdown-native, minimal config, modern | Requires 3 dev dependencies |
| pdoc | Zero config, single dependency | Limited navigation control; no nav for ADRs |

## Decision

Adopt **MkDocs + mkdocstrings + mkdocs-material** as dev-only dependencies.

- `mkdocs` builds the static site from `docs/*.md` files
- `mkdocstrings[python]` renders docstrings inline using the `:::` directive
- `mkdocs-material` provides the theme (widely adopted, accessible, searchable)

All three are **dev dependencies only** — they are never imported by the module and are not required by callers.

The ADR pages (`docs/adr/*.md`) are included in the navigation as-is, with no modifications.

## Consequences

- Three new entries in `[dependency-groups] dev` in `pyproject.toml`
- A `mkdocs.yml` at the project root configures the site structure
- Documentation is served locally with `uv run mkdocs serve` and built statically with `uv run mkdocs build`
- The generated `site/` directory is gitignored
- No changes to the public interface or production code
