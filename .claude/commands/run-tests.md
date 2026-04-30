# /run-tests — Run the test suite with coverage

Runs the `hanel_warehouse_gateway` module tests and shows a coverage report.

## Usage

```
/run-tests
```

Or for a specific module:

```
/run-tests transport
```

## Workflow

### Step 1 — Check prerequisites

Verify that:
- The package is installed in editable mode (`uv pip show hanel-warehouse-gateway`)
- `pytest`, `pytest-cov` and `responses` are installed

If missing: suggest `uv sync`.

### Step 2 — Run tests

```bash
uv run pytest tests/ --ignore=tests/test_mock_server.py --tb=short -q --cov=src/hanel_warehouse_gateway --cov-report=term-missing
```

For a specific module (e.g. `transport`):

```bash
uv run pytest tests/test_transport.py --tb=short -v --cov=src/hanel_warehouse_gateway/transport --cov-report=term-missing
```

### Step 3 — Analyse results

Show:
- Test count: passed / failed / skipped
- Coverage per file (with uncovered lines)
- Total coverage vs threshold (80%)

### Step 4 — Triage failures

For each failing test:
- Show the test name and reason for failure
- Identify whether it is a regression test or a new test
- Suggest where to look for the fix

### Step 5 — Final report

```
## Test Results — <timestamp>

Tests: ✅ N passed / ❌ N failed / ⏭ N skipped

Coverage:
  config.py          95%
  exceptions.py      100%
  models.py          100%
  _xml.py            87%   ← lines 45-48, 92
  transport.py       78%   ← lines 112-120 (retry path)
  operations.py      82%
  gateway.py         90%
  TOTAL:             88%   ✅ (threshold: 80%)

Failures:
  [list of failing tests with context]
```

## Notes

- The minimum coverage threshold is 80% (configured in `pyproject.toml`)
- Tests must not require connectivity to the t-Server
- If a test fails for environmental reasons (missing dependency), report it separately from real failures
