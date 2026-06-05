# Claude Slash Commands

This project defines four slash commands in `.claude/commands/`. Each command automates a repetitive development workflow so it can be triggered with a single instruction.

---

## `/new-operation` {#new-operation}

**File:** `.claude/commands/new-operation.md`

**Trigger:** when adding a new SOAP operation to the module.

**Automated workflow:**

1. Asks for the SOAP operation name and the corresponding Python method
2. Creates the envelope template in `_xml.py` (`build_*` + `parse_*`)
3. Adds the method in `operations.py`
4. Adds the public method in `gateway.py`
5. Creates the XML fixture in `tests/fixtures/`
6. Creates tests in `test_xml.py` and `test_operations.py`
7. Suggests whether a new ADR is needed

---

## `/check-adr`

**File:** `.claude/commands/check-adr.md`

**Trigger:** periodic audit or before opening a PR.

**Automated workflow:**

1. Reads all ADRs in `docs/adr/`
2. Compares decisions against the current code in `src/`
3. Produces a report with: ✅ aligned / ⚠️ drift detected / ❌ contradiction
4. For each drift, suggests whether to update the code or the ADR

---

## `/soap-fixture`

**File:** `.claude/commands/soap-fixture.md`

**Trigger:** when an XML fixture for a t-Server response is needed.

**Automated workflow:**

1. Asks for the SOAP operation name
2. Generates a plausible XML fixture based on the response structure documented in `docs/requirements/`
3. Saves the file to `tests/fixtures/response_<operation>_ok.xml`
4. Also generates a version with `returnValue != 0` and one with a SOAP fault

---

## `/run-tests`

**File:** `.claude/commands/run-tests.md`

**Trigger:** run the test suite with a coverage report.

**Automated workflow:**

1. Runs `pytest tests/ --tb=short -q --cov=src/hanel_warehouse_gateway --cov-report=term-missing`
2. Shows failing tests with context
3. Shows coverage per module
4. Warns if coverage drops below the configured threshold (80%)
