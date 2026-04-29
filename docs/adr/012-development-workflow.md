# ADR-012 — Workflow di sviluppo

**Status:** Accettato

## Contesto

Questo modulo è sviluppato con un mix di contributi umani e agenti Claude. Senza un workflow esplicito, le due modalità di lavoro possono produrre modifiche incoerenti (dipendenze aggiunte senza ADR, interfaccia pubblica cambiata senza bump di versione). Questo ADR definisce i workflow standard per le operazioni più comuni.

## Workflow 1 — Aggiungere una nuova operazione SOAP

1. Verificare che l'operazione non esista già (consultare `docs/requirements.md` §3 e `operations.py`)
2. Se l'operazione introduce un nuovo pattern non coperto dagli ADR esistenti → creare un nuovo ADR
3. Aggiungere i dataclass necessari in `models.py`
4. Aggiungere il template envelope e la funzione di parsing in `_xml.py`
5. Implementare la funzione in `operations.py`
6. Esporre il metodo pubblico in `gateway.py`
7. Creare la fixture XML in `tests/fixtures/`
8. Scrivere i test in `test_xml.py` e `test_operations.py`
9. Aggiornare `CLAUDE.md` se cambia la struttura o i comandi

Alternativa rapida: usare il comando `/new-operation`.

## Workflow 2 — Modificare l'interfaccia pubblica

L'interfaccia pubblica è `HanelWarehouseGateway` e i dataclass pubblici in `models.py`.

1. **Obbligatorio:** creare o aggiornare un ADR che documenta il motivo della modifica
2. Modificare la firma del metodo o il dataclass
3. Aggiornare i type hints e le docstring
4. Eseguire bump di versione in `pyproject.toml` (minor per nuovi metodi, major per breaking changes)
5. Aggiornare i test che dipendono dall'interfaccia modificata
6. Aggiornare `CLAUDE.md` sezione comandi se cambia l'interfaccia pubblica

## Workflow 3 — Aggiungere o modificare un parametro di configurazione

1. Aggiungere il campo in `GatewayConfig` (`config.py`) con tipo e default
2. Aggiungere la validazione in `__post_init__` se necessaria
3. Aggiornare ADR-003 con il nuovo parametro
4. Aggiornare `CLAUDE.md` con il nuovo parametro
5. Aggiungere test in `test_config.py`

## Workflow 4 — Correggere un bug nel parsing XML

1. Creare o aggiornare la fixture XML in `tests/fixtures/` per riprodurre il bug
2. Scrivere un test che fallisce con la fixture (red)
3. Correggere la funzione `parse_*()` in `_xml.py`
4. Verificare che il test passi (green)
5. Se la correzione rivela un'assunzione sbagliata documentata in un ADR → aggiornare l'ADR

## Workflow 5 — Aggiornare le istruzioni Claude

1. Modificare i file in `.claude/agents/` o `.claude/commands/` direttamente
2. Se la modifica riflette un cambiamento architetturale → aggiornare l'ADR corrispondente (ADR-010 o ADR-011)
3. Se la modifica riflette un cambiamento ai comandi di sviluppo → aggiornare anche `CLAUDE.md`

## Regole trasversali

- **Nessuna dipendenza esterna senza ADR.** Dipendenze di produzione (`requests` è l'unica consentita).
- **Nessuna modifica a `__init__.py` exports senza revisione.** L'interfaccia pubblica è contrattuale.
- **I test non usano `requests` reali.** Ogni chiamata HTTP nei test è intercettata da `responses`.
- **Gli ADR non si cancellano.** Se una decisione è superata, lo status diventa `Superseded` con riferimento al nuovo ADR.

## Conseguenze

- Ogni tipo di modifica ha un percorso chiaro da seguire
- Gli agenti Claude che usano `/check-adr` possono rilevare deviazioni da questi workflow
- I workflow sono documenti vivi: aggiornare questo ADR se il processo cambia
