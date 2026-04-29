# /run-tests — Esegui la suite di test con coverage

Esegue i test del modulo `hanel_warehouse_gateway` e mostra un report di coverage.

## Utilizzo

```
/run-tests
```

Oppure per un modulo specifico:

```
/run-tests transport
```

## Workflow

### Step 1 — Verifica prerequisiti

Controlla che:
- Il package sia installato in editable mode (`pip show hanel-warehouse-gateway`)
- `pytest`, `pytest-cov` e `responses` siano installati

Se mancano: suggerisce `pip install -e ".[dev]"`.

### Step 2 — Esecuzione test

```bash
pytest tests/ --tb=short -q --cov=src/hanel_warehouse_gateway --cov-report=term-missing
```

Per un modulo specifico (es. `transport`):

```bash
pytest tests/test_transport.py --tb=short -v --cov=src/hanel_warehouse_gateway/transport --cov-report=term-missing
```

### Step 3 — Analisi risultati

Mostra:
- Numero test: passati / falliti / skippati
- Coverage per file (con righe non coperte)
- Coverage totale vs soglia (80%)

### Step 4 — Triage failures

Per ogni test fallito:
- Mostra il nome del test e il motivo del fallimento
- Identifica se è un regression test o un test nuovo
- Suggerisce dove guardare per la correzione

### Step 5 — Report finale

```
## Test Results — <timestamp>

Tests: ✅ N passed / ❌ N failed / ⏭ N skipped

Coverage:
  config.py          95%
  exceptions.py      100%
  models.py          100%
  _xml.py            87%   ← righe 45-48, 92
  transport.py       78%   ← righe 112-120 (retry path)
  operations.py      82%
  gateway.py         90%
  TOTALE:            88%   ✅ (soglia: 80%)

Failures:
  [lista test falliti con contesto]
```

## Note

- La soglia minima di coverage è 80% (configurata in `pyproject.toml`)
- I test non devono richiedere connettività al t-Server
- Se un test fallisce per motivi ambientali (dipendenza mancante), segnalarlo separatamente dai failure reali
