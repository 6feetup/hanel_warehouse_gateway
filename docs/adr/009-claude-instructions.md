# ADR-009 — CLAUDE.md: istruzioni operative per agenti Claude

**Status:** Accettato

## Contesto

Più agenti Claude Code possono lavorare su questo repository in sessioni diverse. Senza un file `CLAUDE.md` alla radice, ogni agente deve ricavare il contesto da zero esplorando i file. Un `CLAUDE.md` ben strutturato riduce l'esplorazione iniziale e previene errori ricorrenti.

## Decisione

Creare `CLAUDE.md` alla radice del repository con le informazioni operative essenziali per agenti Claude che lavorano su questo progetto.

## Contenuto obbligatorio di CLAUDE.md

1. **Descrizione** — scopo del modulo in 2-3 righe
2. **Struttura directory** — responsabilità di ogni file (derivata da ADR-001)
3. **Comandi di sviluppo** — install, test, lint, type check
4. **Vincoli critici** — regole che non devono essere violate senza un nuovo ADR
5. **Riferimenti ADR** — link agli ADR principali con una riga di descrizione ciascuno

## Vincoli critici da includere

- Non aggiungere dipendenze esterne senza un ADR (zeep, lxml, pydantic, structlog sono esplicitamente escluse)
- Non modificare l'interfaccia pubblica di `HanelWarehouseGateway` senza un ADR
- Non aggiungere handler al logger (libreria: NullHandler only)
- I template XML vivono in `_xml.py` — non dispersi in altri file
- `__init__.py` espone solo: `HanelWarehouseGateway`, i dataclass pubblici, le eccezioni

## Conseguenze

- Gli agenti Claude hanno istruzioni operative chiare senza dover leggere tutti gli ADR
- I vincoli critici prevengono derive architetturali nelle sessioni automatizzate
- `CLAUDE.md` deve essere aggiornato quando cambia struttura, comandi, o vincoli
