# /soap-fixture — Genera fixture XML per operazioni SOAP

Genera file XML di risposta plausibili da usare come fixture nei test del modulo `hanel_warehouse_gateway`.

## Utilizzo

```
/soap-fixture <operation_name>
```

Esempio: `/soap-fixture sendJobsReqV01`

Oppure senza argomenti per scegliere interattivamente.

## Operazioni supportate

| Operazione SOAP | Metodo Python | Fixture da generare |
|-----------------|---------------|---------------------|
| `sendAPDReqV01` | `register_article` | ok, error |
| `sendJobsReqV01` | `send_movement_order` | ok, error |
| `readAllJobsReqV01` (mode=0) | `get_all_orders` | ok con più ordini, vuoto |
| `readAllJobsReqV01` (mode=1) | `get_completed_movements` | ok con più ordini completati, vuoto |
| `readAllAMDReqV01` | `get_inventory` | ok con più record, vuoto |
| `deleteJobReqV01` | `cancel_order` | ok, error |

## Workflow

### Step 1 — Lettura requisiti

Leggi la sezione corrispondente in `docs/requirements.md` per la struttura della risposta attesa.

### Step 2 — Generazione fixture

Per ogni operazione, genera **tre fixture**:

1. **`response_<op>_ok.xml`** — risposta happy path con `returnValue` = 0 e dati plausibili
2. **`response_<op>_error.xml`** — risposta con `returnValue` != 0 (es. 1 o -1) e messaggio di errore
3. **`response_soap_fault.xml`** — se non esiste già, genera una volta sola

Per le operazioni che restituiscono liste (`readAllJobsReqV01`, `readAllAMDReqV01`):
- Fixture ok con almeno 2 elementi
- Fixture `_empty.xml` con lista vuota

### Step 3 — Salvataggio

Salva le fixture in `tests/fixtures/` con naming:
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

### Step 4 — Riepilogo

Elenca i file creati e indica quali test possono usarli.

## Nota sui namespace

Le fixture devono usare i namespace corretti:
- `xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"`
- `xmlns:main="http://main.jws.com.hanel.de"`
- `xmlns:xsd="http://main.jws.com.hanel.de/xsd"`
