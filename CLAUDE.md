# CLAUDE.md — hanel_warehouse_gateway

Modulo Python per la comunicazione con il magazzino automatico Hanel via SOAP. Espone un'interfaccia Python tipizzata e nasconde completamente i dettagli SOAP al chiamante.

## Struttura directory

```
src/hanel_warehouse_gateway/
├── __init__.py      ← espone: HanelWarehouseGateway, dataclass pubblici, eccezioni
├── gateway.py       ← Layer 3: interfaccia pubblica, unico punto di contatto
├── operations.py    ← Layer 2: mapping operazioni SOAP, serializzazione/deserializzazione
├── transport.py     ← Layer 1: HTTP POST, retry, timeout, logging payload
├── models.py        ← dataclass: MovementLine, MovementLineResult, MovementResult, StockRecord
├── exceptions.py    ← gerarchia HanelGatewayError
├── config.py        ← GatewayConfig dataclass + validazione __post_init__
└── _xml.py          ← PRIVATO: template envelope f-string, parsing ElementTree
tests/
├── fixtures/        ← file XML di risposta del t-Server (fonte di verità per i parser)
├── test_config.py
├── test_exceptions.py
├── test_models.py
├── test_xml.py
├── test_transport.py
└── test_operations.py
docs/
├── requirements.md  ← specifica tecnica completa (leggere prima di implementare)
└── adr/             ← Architecture Decision Records (001–012)
```

## Comandi di sviluppo

```bash
# Installazione in editable mode con dipendenze dev
pip install -e ".[dev]"

# Esecuzione test
pytest tests/ --tb=short -q

# Test con coverage
pytest tests/ --cov=src/hanel_warehouse_gateway --cov-report=term-missing

# Type checking
mypy src/hanel_warehouse_gateway/

# Lint
ruff check src/ tests/
```

## Configurazione (parametri principali)

I parametri **volatili e i secret** (`endpoint_url`, `test_mode`, `test_prefix`) vivono nel file `.env` (non committato). Usare `GatewayConfig.from_env()` per caricarli:

```python
# Uso standard — legge da .env o variabili d'ambiente
client = HanelWarehouseGateway(GatewayConfig.from_env())

# Con override espliciti (es. nei test)
client = HanelWarehouseGateway(GatewayConfig.from_env({
    "endpoint_url": "http://mock/",
    "test_mode": True,
}))
```

File `.env` (non committare — vedi `.env.example` per il template):

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

Parametri statici con default (passabili come override):

| Parametro | Default | Note |
|---|---|---|
| `timeout_seconds` | 30 | |
| `retry_attempts` | 3 | |
| `retry_delay_seconds` | 2.0 | |
| `log_level` | `INFO` | |
| `log_soap_payloads` | `False` | |
| `validation_truncate` | `False` | `True` → tronca a 40 chars invece di raise |

## Vincoli critici

- **NO dipendenze esterne di produzione** oltre a `requests` e `python-dotenv`. zeep, lxml, pydantic, structlog sono esplicitamente escluse. Aggiungere una dipendenza richiede un ADR.
- **NO modifica all'interfaccia pubblica** (`HanelWarehouseGateway`, dataclass in `models.py`) senza un ADR e bump di versione.
- **NO `endpoint_url`, `test_mode`, credenziali nel codice sorgente o in file committati**. Sempre da variabili d'ambiente / `.env`.
- **NO handler al logger**: il modulo è una libreria e usa solo `NullHandler`. Il chiamante configura i propri handler.
- **I template XML vivono in `_xml.py`**: nessun envelope XML altrove.
- **`__init__.py` espone solo**: `HanelWarehouseGateway`, `MovementLine`, `MovementLineResult`, `MovementResult`, `StockRecord`, e le eccezioni `HanelGateway*`.
- **I test non fanno HTTP reale**: ogni chiamata `requests` nei test è intercettata da `responses`.
- **Gli ADR non si cancellano**: se una decisione cambia, aggiornare lo status a `Superseded` con riferimento al nuovo ADR.

## ADR principali

| ADR | Decisione |
|-----|-----------|
| [001](docs/adr/001-packaging-structure.md) | `pyproject.toml` + layout `src/` |
| [002](docs/adr/002-soap-transport.md) | `requests` + XML manuale (no zeep) |
| [003](docs/adr/003-configuration.md) | `GatewayConfig` dataclass da dict |
| [004](docs/adr/004-xml-construction-parsing.md) | f-string template + ElementTree |
| [005](docs/adr/005-error-handling-retry.md) | Gerarchia eccezioni + retry solo su errori di rete |
| [006](docs/adr/006-logging.md) | `logging` stdlib, NullHandler, no handler di default |
| [007](docs/adr/007-testing-strategy.md) | `pytest` + `unittest.mock` + `responses` |
| [008](docs/adr/008-input-validation.md) | Default raise su campi > 40 chars; truncate opt-in |
| [009](docs/adr/009-claude-instructions.md) | Questo file |
| [010](docs/adr/010-claude-agents.md) | Agenti specializzati in `.claude/agents/` |
| [011](docs/adr/011-claude-commands.md) | Comandi slash in `.claude/commands/` |
| [012](docs/adr/012-development-workflow.md) | Workflow per modifiche comuni |

## Comandi slash disponibili

- `/new-operation` — scaffold completo per una nuova operazione SOAP
- `/check-adr` — verifica coerenza ADR vs codice attuale
- `/soap-fixture` — genera fixture XML per un'operazione
- `/run-tests` — esegue pytest con coverage e mostra summary

## Note operative

- Il t-Server non ha ambiente di test separato. Usare `test_mode=True` per ordini identificabili dagli operatori.
- Il modulo **non è thread-safe**. Istanziare un client per thread se necessario il parallelismo.
- `get_inventory()` è l'unico modo per rilevare movimenti manuali eseguiti direttamente alla console del magazzino.
- `actual_quantity < nominal_quantity` in `MovementLineResult` indica stock insufficiente: la gestione è responsabilità del chiamante.
