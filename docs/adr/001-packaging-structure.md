# ADR-001 — Packaging e struttura del modulo Python

**Status:** Accettato

## Contesto

Il progetto è un modulo Python autonomo che espone un'interfaccia per comunicare con il magazzino automatico Hanel via SOAP. Prima di scrivere codice è necessario stabilire la struttura di packaging e la disposizione dei file sorgente.

## Opzioni valutate

| Opzione | Pro | Contro |
|---|---|---|
| `setup.py` legacy | Familiare, universalmente supportato | Deprecato, non standard PEP 621 |
| `setup.cfg` | Separazione config da codice | Semi-legacy, soppiantato da pyproject.toml |
| `pyproject.toml` (PEP 517/621) | Standard moderno, supportato da pip/build/hatch/uv | Nessuno rilevante |

## Decisione

Adottiamo **`pyproject.toml`** con layout `src/` (PEP 517/621).

Il layout `src/` evita che il package sia importabile direttamente dalla radice del progetto durante lo sviluppo, forzando l'installazione in editable mode (`pip install -e .`) e riducendo i falsi positivi nei test.

## Struttura directory

```
hanel_warehouse_gateway/           ← radice del repository
├── src/
│   └── hanel_warehouse_gateway/
│       ├── __init__.py            ← espone solo HanelWarehouseGateway e i dataclass pubblici
│       ├── gateway.py             ← Layer 3: HanelWarehouseGateway (interfaccia pubblica)
│       ├── operations.py          ← Layer 2: mapping operazioni SOAP
│       ├── transport.py           ← Layer 1: client HTTP/SOAP, retry, timeout
│       ├── models.py              ← dataclass: MovementLine, MovementResult, StockRecord…
│       ├── exceptions.py          ← gerarchia HanelGatewayError
│       ├── config.py              ← GatewayConfig dataclass + validazione
│       └── _xml.py                ← helper privato: costruzione envelope + parsing risposta
├── tests/
│   ├── fixtures/                  ← XML di risposta per i test
│   ├── test_config.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   ├── test_xml.py
│   ├── test_transport.py
│   └── test_operations.py
├── docs/
│   ├── requirements.md
│   └── adr/
├── CLAUDE.md
├── pyproject.toml
└── .claude/
    ├── agents/
    └── commands/
```

## Responsabilità dei file

| File | Responsabilità |
|---|---|
| `gateway.py` | Unico punto di contatto per il chiamante; delega a `operations.py` |
| `operations.py` | Costruisce la chiamata SOAP specifica, deserializza la risposta |
| `transport.py` | Esegue HTTP POST, gestisce retry e timeout, logga payload |
| `models.py` | Definisce tutti i dataclass pubblici e interni |
| `exceptions.py` | Definisce la gerarchia di eccezioni |
| `config.py` | Valida e normalizza la configurazione in ingresso |
| `_xml.py` | Template f-string degli envelope + funzioni di parsing ElementTree |

## Conseguenze

- Installazione in editable mode richiesta per sviluppo: `pip install -e ".[dev]"`
- Il package è importabile solo dopo installazione, non direttamente da `src/`
- `__init__.py` espone esclusivamente `HanelWarehouseGateway`, i dataclass pubblici e le eccezioni — niente di `_xml.py` o dei layer interni
