# ADR-010 — Specialized Claude agents

**Status:** Accepted

## Context

Some recurring tasks in this module's development cycle require specific knowledge of the SOAP domain, the t-Server XML structure, and project conventions. Specialized Claude agents in `.claude/agents/` can execute these tasks with pre-loaded context, reducing the instructions needed each time.

## Decision

Define three specialized agents in `.claude/agents/`:

### `soap-tester`

**File:** `.claude/agents/soap-tester.md`

**Purpose:** generates unit and integration tests for SOAP operations.

**Capabilities:**
- Given an operation (e.g. `send_movement_order`), generates the corresponding XML response fixture in `tests/fixtures/`
- Generates `test_xml.py` tests for `build_*` and `parse_*`
- Generates `test_operations.py` tests with `responses` for HTTP mocking
- Verifies that tests cover: happy path, `returnValue != 0`, SOAP fault, network error

### `adr-reviewer`

**File:** `.claude/agents/adr-reviewer.md`

**Purpose:** verifies consistency between ADRs and the implemented code.

**Capabilities:**
- Reads ADRs and source code
- Reports drift (e.g. external dependency added without an ADR, undocumented config parameter)
- Proposes ADR updates if the code has evolved in a justified way

### `integration-checker`

**File:** `.claude/agents/integration-checker.md`

**Purpose:** analyzes the impact of a change to the public interface.

**Capabilities:**
- Given a proposed change to a `HanelWarehouseGateway` method signature, evaluates backward compatibility
- Verifies that public dataclasses have no breaking changes
- Verifies that introduced exceptions are subclasses of `HanelGatewayError`

## Structure of each agent file

```markdown
---
name: <name>
description: <one-line description>
---

<system prompt with project context, constraints, expected output format>
```

## Consequences

- Recurring tasks can be delegated to agents without repeating context
- Agents use only file read and write tools — they do not execute system commands
- Agent maintenance is the team's responsibility: update the files if the architecture changes
