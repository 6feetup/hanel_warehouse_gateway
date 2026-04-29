# ADR-007 — Strategia di testing

**Status:** Accettato

## Contesto

Il modulo comunica con un sistema esterno (t-Server Hanel) che non è disponibile in ambiente di sviluppo e non ha un ambiente di test separato. I test devono essere eseguibili senza connettività al magazzino.

## Opzioni valutate

| Framework | Pro | Contro |
|---|---|---|
| `unittest` puro | Stdlib, zero dipendenze | Verboso, fixture più complesse |
| `pytest` | Fixture potenti, plugin ecosystem, output leggibile | Dipendenza dev |
| `pytest` + `pytest-mock` | Mock API più pulita | Dipendenza extra, `unittest.mock` è sufficiente |
| `responses` (mock HTTP) | Intercetta `requests` senza patch manuale | Dipendenza dev extra ma necessaria |

## Decisione

Adottiamo **`pytest`** + **`unittest.mock`** + **`responses`**.

`responses` è la scelta corretta per testare `transport.py`: intercetta le chiamate HTTP a livello di `requests` senza richiedere patch manuali di `requests.post`.

## Livelli di test

### 1. Unit test (no HTTP)

Testano componenti isolati:
- `test_config.py` — validazione `GatewayConfig`, chiavi mancanti, tipi errati
- `test_exceptions.py` — costruzione eccezioni, attributi obbligatori
- `test_models.py` — costruzione dataclass, valori di default
- `test_xml.py` — `build_*()` produce XML atteso; `parse_*()` estrae i campi corretti da fixture XML

### 2. Integration test (HTTP mockato)

Testano il flusso completo dalla chiamata pubblica alla deserializzazione, con HTTP intercettato da `responses`:
- `test_transport.py` — retry su errori di rete, classificazione errori HTTP
- `test_operations.py` — ogni operazione SOAP: input → envelope corretto → parsing risposta → output atteso

### 3. End-to-end

Non incluso. Il `test_mode=True` con prefisso `TEST_` è il meccanismo per testare contro il sistema reale senza impattare lo stock.

## Fixture XML

Le fixture risiedono in `tests/fixtures/` come file `.xml`:

```
tests/fixtures/
├── response_send_apd_ok.xml
├── response_send_apd_error.xml
├── response_send_jobs_ok.xml
├── response_read_jobs_mode0.xml
├── response_read_jobs_mode1.xml
├── response_read_amd.xml
├── response_delete_job_ok.xml
└── response_soap_fault.xml
```

Le fixture rappresentano risposte reali o plausibili del t-Server e sono la fonte di verità per i parser.

## Configurazione pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short -q"
```

Coverage configurata tramite `pytest-cov`:

```toml
[tool.coverage.run]
source = ["src/hanel_warehouse_gateway"]
branch = true

[tool.coverage.report]
fail_under = 80
```

## Conseguenze

- I test sono eseguibili offline senza accesso al t-Server
- Le fixture XML documentano implicitamente la struttura delle risposte attese
- Aggiungere una nuova operazione SOAP richiede: fixture XML + test in `test_xml.py` + test in `test_operations.py`
