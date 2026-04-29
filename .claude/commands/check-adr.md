# /check-adr — Verifica coerenza ADR vs codice

Esegue un audit di coerenza tra le decisioni architetturali documentate in `docs/adr/` e il codice attuale in `src/`.

## Utilizzo

```
/check-adr
```

Oppure per un ADR specifico:

```
/check-adr 002
```

## Workflow

### Step 1 — Lettura ADR

Leggi tutti i file in `docs/adr/` (o solo quello specificato).

### Step 2 — Lettura codice

Per ogni ADR, leggi i file sorgente rilevanti:

| ADR | File da leggere |
|-----|-----------------|
| 001 | `pyproject.toml`, struttura directory |
| 002 | `transport.py`, `pyproject.toml` (dipendenze) |
| 003 | `config.py`, `gateway.py` |
| 004 | `_xml.py` |
| 005 | `exceptions.py`, `transport.py` |
| 006 | `__init__.py`, tutti i file (cerca `print()`, `addHandler`) |
| 007 | `tests/` (cerca `requests.post` non mockato) |
| 008 | `operations.py` (cerca validazione lunghezza) |

### Step 3 — Classificazione

Per ogni punto verificato:
- ✅ **Allineato** — il codice rispecchia la decisione
- ⚠️ **Deriva** — divergenza rilevata, potenzialmente giustificata
- ❌ **Contraddizione** — violazione esplicita della decisione

### Step 4 — Report

Produce il report strutturato (vedi formato nell'agente `adr-reviewer`).

### Step 5 — Suggerimenti

Per ogni deriva o contraddizione, propone:
- Se il codice è corretto e l'ADR è obsoleto → suggerisce aggiornamento ADR
- Se il codice diverge senza giustificazione → suggerisce correzione del codice

## Note

- Questo comando è read-only: non modifica file
- Per modifiche usa `/new-operation` o agisci manualmente seguendo ADR-012
