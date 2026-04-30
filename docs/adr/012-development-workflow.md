# ADR-012 — Development workflow

**Status:** Accepted

## Context

This module is developed with a mix of human contributions and Claude agents. Without an explicit workflow, the two working modes can produce inconsistent changes (dependencies added without an ADR, public interface changed without a version bump). This ADR defines the standard workflows for the most common operations.

## Workflow 1 — Adding a new SOAP operation

1. Verify the operation does not already exist (consult `docs/requirements.md` §3 and `operations.py`)
2. If the operation introduces a new pattern not covered by existing ADRs → create a new ADR
3. Add the required dataclasses in `models.py`
4. Add the envelope template and parsing function in `_xml.py`
5. Implement the function in `operations.py`
6. Expose the public method in `gateway.py`
7. Create the XML fixture in `tests/fixtures/`
8. Write tests in `test_xml.py` and `test_operations.py`
9. Update `CLAUDE.md` if the structure or commands change

Quick alternative: use the `/new-operation` command.

## Workflow 2 — Modifying the public interface

The public interface is `HanelWarehouseGateway` and the public dataclasses in `models.py`.

1. **Required:** create or update an ADR documenting the reason for the change
2. Modify the method signature or dataclass
3. Update type hints and docstrings
4. Bump the version in `pyproject.toml` (minor for new methods, major for breaking changes)
5. Update tests that depend on the modified interface
6. Update the `CLAUDE.md` commands section if the public interface changes

## Workflow 3 — Adding or modifying a configuration parameter

1. Add the field in `GatewayConfig` (`config.py`) with type and default
2. Add validation in `__post_init__` if needed
3. Update ADR-003 with the new parameter
4. Update `CLAUDE.md` with the new parameter
5. Add tests in `test_config.py`

## Workflow 4 — Fixing a bug in XML parsing

1. Create or update the XML fixture in `tests/fixtures/` to reproduce the bug
2. Write a failing test with the fixture (red)
3. Fix the `parse_*()` function in `_xml.py`
4. Verify the test passes (green)
5. If the fix reveals a wrong assumption documented in an ADR → update the ADR

## Workflow 5 — Updating Claude instructions

1. Edit files in `.claude/agents/` or `.claude/commands/` directly
2. If the change reflects an architectural modification → update the corresponding ADR (ADR-010 or ADR-011)
3. If the change reflects a change to development commands → also update `CLAUDE.md`

## Cross-cutting rules

- **No external dependencies without an ADR.** Production dependencies (`requests` is the only one allowed).
- **No changes to `__init__.py` exports without review.** The public interface is contractual.
- **Tests do not use real `requests`.** Every HTTP call in tests is intercepted by `responses`.
- **ADRs are never deleted.** If a decision is superseded, its status becomes `Superseded` with a reference to the new ADR.

## Consequences

- Every type of change has a clear path to follow
- Claude agents using `/check-adr` can detect deviations from these workflows
- Workflows are living documents: update this ADR if the process changes
