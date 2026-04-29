# /new-operation — Scaffold nuova operazione SOAP

Questo comando guida la creazione completa di una nuova operazione SOAP nel modulo `hanel_warehouse_gateway`.

## Utilizzo

```
/new-operation
```

Oppure con argomenti:

```
/new-operation <soap_operation_name> <python_method_name>
```

Esempio: `/new-operation sendAPDReqV01 register_article`

## Workflow

### Step 1 — Raccolta informazioni

Se gli argomenti non sono forniti, chiedi:
1. Nome dell'operazione SOAP (es. `sendAPDReqV01`)
2. Nome del metodo Python pubblico (es. `register_article`)
3. Tipo di output: `bool`, `list[MovementResult]`, `list[StockRecord]`, o altro
4. Parametri in input (nome, tipo, constraint)
5. Incolla l'envelope XML di riferimento (opzionale)

### Step 2 — Verifica prerequisiti

- Controlla che il metodo non esista già in `gateway.py`
- Controlla che l'operazione non esista già in `operations.py`
- Se esistono dataclass simili in `models.py`, segnalarlo

### Step 3 — Creazione file

Crea o modifica nell'ordine:

1. **`src/hanel_warehouse_gateway/models.py`** — aggiunge i dataclass necessari (se nuovi)
2. **`src/hanel_warehouse_gateway/_xml.py`** — aggiunge `build_<operation>()` e `parse_<operation>()`
3. **`src/hanel_warehouse_gateway/operations.py`** — aggiunge la funzione dell'operazione
4. **`src/hanel_warehouse_gateway/gateway.py`** — aggiunge il metodo pubblico
5. **`src/hanel_warehouse_gateway/__init__.py`** — espone i nuovi dataclass pubblici (se necessario)
6. **`tests/fixtures/response_<operation>_ok.xml`** — fixture XML happy path
7. **`tests/fixtures/response_<operation>_error.xml`** — fixture con returnValue != 0
8. **`tests/test_xml.py`** — test per `build_*` e `parse_*`
9. **`tests/test_operations.py`** — test di integrazione con HTTP mockato

### Step 4 — Verifica ADR

Controlla se la nuova operazione introduce:
- Una nuova dipendenza → richiede ADR
- Un nuovo pattern di risposta non coperto da ADR-004 → richiede aggiornamento ADR
- Un nuovo tipo di eccezione → richiede aggiornamento ADR-005

### Step 5 — Riepilogo

Elenca tutti i file creati/modificati con una riga di descrizione per ciascuno.
