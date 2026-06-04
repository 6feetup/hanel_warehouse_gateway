# /soap-fixture — Generate XML fixtures for SOAP operations

Generates plausible XML response files to use as fixtures in the `hanel_warehouse_gateway` module tests.

## Usage

```
/soap-fixture <operation_name>
```

Example: `/soap-fixture sendJobsReqV01`

Or without arguments to choose interactively.

## Supported operations

| SOAP operation | Python method | Fixtures to generate |
|----------------|---------------|----------------------|
| `sendAPDReqV01` | `register_article` | ok, error |
| `sendJobsReqV01` | `send_movement_order` | ok, error |
| `readAllJobsReqV01` (mode=0) | `get_all_orders` | ok with multiple orders, empty |
| `readAllJobsReqV01` (mode=1) | `get_completed_movements` | ok with multiple completed orders, empty |
| `readAllAMDReqV01` | `get_inventory` | ok with multiple records, empty |
| `deleteJobReqV01` | `cancel_order` | ok, error |

## Workflow

### Step 1 — Read requirements

Read the corresponding section in `docs/requirements/` for the expected response structure.

### Step 2 — Generate fixtures

For each operation, generate **three fixtures**:

1. **`response_<op>_ok.xml`** — happy path response with `returnValue` = 0 and plausible data
2. **`response_<op>_error.xml`** — response with `returnValue` != 0 (e.g. 1 or -1) and error message
3. **`response_soap_fault.xml`** — if it does not already exist, generate once only

For operations that return lists (`readAllJobsReqV01`, `readAllAMDReqV01`):
- Ok fixture with at least 2 elements
- `_empty.xml` fixture with an empty list

### Step 3 — Save

Save fixtures in `tests/fixtures/` with naming:
- `response_send_apd_ok.xml`
- `response_send_apd_error.xml`
- `response_send_jobs_ok.xml`
- `response_read_jobs_mode0_ok.xml`
- `response_read_jobs_mode0_empty.xml`
- `response_read_jobs_mode1_ok.xml`
- `response_read_amd_ok.xml`
- `response_read_amd_empty.xml`
- `response_delete_job_ok.xml`
- `response_delete_job_error.xml`
- `response_soap_fault.xml`

### Step 4 — Summary

List the files created and indicate which tests can use them.

## Namespace note

Fixtures must use the correct namespaces:
- `xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"`
- `xmlns:main="http://main.jws.com.hanel.de"`
- `xmlns:xsd="http://main.jws.com.hanel.de/xsd"`
