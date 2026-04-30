# ADR-009 — CLAUDE.md: operational instructions for Claude agents

**Status:** Accepted

## Context

Multiple Claude Code agents may work on this repository across different sessions. Without a `CLAUDE.md` file at the root, each agent must derive context from scratch by exploring files. A well-structured `CLAUDE.md` reduces initial exploration and prevents recurring mistakes.

## Decision

Create `CLAUDE.md` at the repository root with the essential operational information for Claude agents working on this project.

## Required content of CLAUDE.md

1. **Description** — module purpose in 2-3 lines
2. **Directory structure** — responsibility of each file (derived from ADR-001)
3. **Development commands** — install, test, lint, type check
4. **Critical constraints** — rules that must not be violated without a new ADR
5. **ADR references** — links to the key ADRs with a one-line description each

## Critical constraints to include

- Do not add external dependencies without an ADR (zeep, lxml, pydantic, structlog are explicitly excluded)
- Do not modify the public interface of `HanelWarehouseGateway` without an ADR
- Do not add handlers to the logger (library: NullHandler only)
- XML templates live in `_xml.py` — not scattered across other files
- `__init__.py` exposes only: `HanelWarehouseGateway`, the public dataclasses, the exceptions

## Consequences

- Claude agents have clear operational instructions without having to read all ADRs
- Critical constraints prevent architectural drift in automated sessions
- `CLAUDE.md` must be updated whenever structure, commands, or constraints change
