# ADR-010 — Agenti Claude specializzati

**Status:** Accettato

## Contesto

Alcune attività ricorrenti nel ciclo di sviluppo di questo modulo richiedono conoscenza specifica del dominio SOAP, della struttura XML del t-Server e delle convenzioni del progetto. Gli agenti Claude specializzati in `.claude/agents/` possono eseguire questi task con contesto pre-caricato, riducendo le istruzioni da fornire ogni volta.

## Decisione

Definire tre agenti specializzati in `.claude/agents/`:

### `soap-tester`

**File:** `.claude/agents/soap-tester.md`

**Scopo:** genera test unitari e di integrazione per operazioni SOAP.

**Capacità:**
- Data un'operazione (es. `send_movement_order`), genera la fixture XML di risposta corrispondente in `tests/fixtures/`
- Genera i test `test_xml.py` per `build_*` e `parse_*`
- Genera i test `test_operations.py` con `responses` per mock HTTP
- Verifica che i test coprono: caso happy path, `returnValue != 0`, SOAP fault, errore di rete

### `adr-reviewer`

**File:** `.claude/agents/adr-reviewer.md`

**Scopo:** verifica la coerenza tra gli ADR e il codice implementato.

**Capacità:**
- Legge gli ADR e il codice sorgente
- Segnala derive (es. dipendenza esterna aggiunta senza ADR, parametro di config non documentato)
- Propone aggiornamenti agli ADR se il codice è evoluto in modo giustificato

### `integration-checker`

**File:** `.claude/agents/integration-checker.md`

**Scopo:** analizza l'impatto di una modifica all'interfaccia pubblica.

**Capacità:**
- Data una modifica proposta alla firma di un metodo di `HanelWarehouseGateway`, valuta la compatibilità backward
- Verifica che i dataclass pubblici non abbiano breaking changes
- Verifica che le eccezioni introdotte siano sottoclassi di `HanelGatewayError`

## Struttura di ogni file agente

```markdown
---
name: <nome>
description: <descrizione una riga>
---

<system prompt con contesto del progetto, vincoli, formato output atteso>
```

## Conseguenze

- I task ricorrenti possono essere delegati agli agenti senza ripetere il contesto
- Gli agenti usano solo strumenti di lettura e scrittura file — non eseguono comandi di sistema
- La manutenzione degli agenti è responsabilità del team: aggiornare i file se cambia l'architettura
