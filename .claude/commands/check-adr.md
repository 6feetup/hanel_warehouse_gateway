# /check-adr — Verify ADR consistency vs code

Runs a consistency audit between the architectural decisions documented in `docs/adr/` and the current code in `src/`.

## Usage

```
/check-adr
```

Or for a specific ADR:

```
/check-adr 002
```

## Workflow

### Step 1 — Read ADRs

Read all files in `docs/adr/` (or only the one specified).

### Step 2 — Read code

For each ADR, read the relevant source files:

| ADR | Files to read |
|-----|---------------|
| 001 | `pyproject.toml`, directory structure |
| 002 | `transport.py`, `pyproject.toml` (dependencies) |
| 003 | `config.py`, `gateway.py` |
| 004 | `_xml.py` |
| 005 | `exceptions.py`, `transport.py` |
| 006 | `__init__.py`, all files (search for `print()`, `addHandler`) |
| 007 | `tests/` (search for unmocked `requests.post`) |
| 008 | `operations.py` (search for length validation) |

### Step 3 — Classification

For each verified point:
- ✅ **Aligned** — the code reflects the decision
- ⚠️ **Drift** — deviation detected, potentially justified
- ❌ **Contradiction** — explicit violation of the decision

### Step 4 — Report

Produce the structured report (see format in the `adr-reviewer` agent).

### Step 5 — Suggestions

For each drift or contradiction, propose:
- If the code is correct and the ADR is outdated → suggest updating the ADR
- If the code deviates without justification → suggest fixing the code

## Notes

- This command is read-only: it does not modify files
- For changes use `/new-operation` or act manually following ADR-012
