# Specialized Claude Agents

This project defines three specialized Claude agents in `.claude/agents/`. Each agent is pre-loaded with domain context to handle recurring tasks without needing to re-describe the project each time.

---

## `soap-tester`

**File:** `.claude/agents/soap-tester.md`

**Purpose:** Generates unit and integration tests for SOAP operations.

**Capabilities:**

- Given an operation name (e.g. `send_movement_order`), generates the corresponding XML response fixture in `tests/fixtures/`
- Generates `test_xml.py` tests for `build_*` and `parse_*` functions
- Generates `test_operations.py` tests with `responses` for HTTP mocking
- Verifies that tests cover: happy path, `returnValue != 0`, SOAP fault, network error

---

## `adr-reviewer`

**File:** `.claude/agents/adr-reviewer.md`

**Purpose:** Verifies consistency between ADRs and the implemented code.

**Capabilities:**

- Reads ADRs and source code
- Reports drift (e.g. external dependency added without an ADR, undocumented config parameter)
- Proposes ADR updates if the code has evolved in a justified way

---

## `integration-checker`

**File:** `.claude/agents/integration-checker.md`

**Purpose:** Analyses the impact of a change to the public interface.

**Capabilities:**

- Given a proposed change to a `HanelWarehouseGateway` method signature, evaluates backward compatibility
- Verifies that public dataclasses have no breaking changes
- Verifies that introduced exceptions are subclasses of `HanelGatewayError`

---

## Agent file structure

Each agent file follows this format:

```markdown
---
name: <name>
description: <one-line description>
---

<system prompt with project context, constraints, expected output format>
```

Agents use only file read and write tools — they do not execute system commands. Update the agent files whenever the architecture changes.
