# /new-operation — Scaffold a new SOAP operation

This command guides the complete creation of a new SOAP operation in the `hanel_warehouse_gateway` module.

## Usage

```
/new-operation
```

Or with arguments:

```
/new-operation <soap_operation_name> <python_method_name>
```

Example: `/new-operation sendAPDReqV01 register_article`

## Workflow

### Step 1 — Gather information

If arguments are not provided, ask:
1. Name of the SOAP operation (e.g. `sendAPDReqV01`)
2. Name of the public Python method (e.g. `register_article`)
3. Output type: `bool`, `list[MovementResult]`, `list[StockRecord]`, or other
4. Input parameters (name, type, constraints)
5. Paste the reference XML envelope (optional)

### Step 2 — Check prerequisites

- Verify the method does not already exist in `gateway.py`
- Verify the operation does not already exist in `operations.py`
- If similar dataclasses exist in `models.py`, flag them

### Step 3 — Create files

Create or modify in order:

1. **`src/hanel_warehouse_gateway/models.py`** — adds the required dataclasses (if new)
2. **`src/hanel_warehouse_gateway/_xml.py`** — adds `build_<operation>()` and `parse_<operation>()`
3. **`src/hanel_warehouse_gateway/operations.py`** — adds the operation function
4. **`src/hanel_warehouse_gateway/gateway.py`** — adds the public method
5. **`src/hanel_warehouse_gateway/__init__.py`** — exposes new public dataclasses (if needed)
6. **`tests/fixtures/response_<operation>_ok.xml`** — happy path XML fixture
7. **`tests/fixtures/response_<operation>_error.xml`** — fixture with returnValue != 0
8. **`tests/test_xml.py`** — tests for `build_*` and `parse_*`
9. **`tests/test_operations.py`** — integration tests with mocked HTTP

### Step 4 — Verify ADRs

Check whether the new operation introduces:
- A new dependency → requires an ADR
- A new response pattern not covered by ADR-004 → requires updating the ADR
- A new exception type → requires updating ADR-005

### Step 5 — Summary

List all files created/modified with a one-line description for each.
