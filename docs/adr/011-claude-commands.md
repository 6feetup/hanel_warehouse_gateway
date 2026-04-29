# ADR-011 — Comandi slash Claude

**Status:** Accettato

## Contesto

Alcune operazioni nel ciclo di sviluppo di questo modulo sono ripetitive e seguono sempre lo stesso schema (aggiungere un'operazione SOAP, verificare gli ADR, generare fixture). I comandi slash Claude in `.claude/commands/` permettono di eseguire questi workflow con un singolo comando invece di descrivere ogni volta le istruzioni.

## Decisione

Definire quattro comandi slash in `.claude/commands/`:

### `/new-operation`

**File:** `.claude/commands/new-operation.md`

**Trigger:** quando si aggiunge una nuova operazione SOAP al modulo.

**Workflow automatizzato:**
1. Chiede il nome dell'operazione SOAP e il metodo Python corrispondente
2. Crea il template envelope in `_xml.py` (`build_*` + `parse_*`)
3. Aggiunge il metodo in `operations.py`
4. Aggiunge il metodo pubblico in `gateway.py`
5. Crea la fixture XML in `tests/fixtures/`
6. Crea i test in `test_xml.py` e `test_operations.py`
7. Suggerisce se è necessario un nuovo ADR

### `/check-adr`

**File:** `.claude/commands/check-adr.md`

**Trigger:** audit periodico o prima di un PR.

**Workflow automatizzato:**
1. Legge tutti gli ADR in `docs/adr/`
2. Confronta le decisioni con il codice attuale in `src/`
3. Produce un report con: ✅ allineato / ⚠️ deriva rilevata / ❌ contraddizione
4. Per ogni deriva, suggerisce se aggiornare il codice o l'ADR

### `/soap-fixture`

**File:** `.claude/commands/soap-fixture.md`

**Trigger:** quando si ha bisogno di una fixture XML per una risposta del t-Server.

**Workflow automatizzato:**
1. Chiede il nome dell'operazione SOAP
2. Genera una fixture XML plausibile basata sulla struttura di risposta documentata in `requirements.md`
3. Salva il file in `tests/fixtures/response_<operation>_ok.xml`
4. Genera anche una versione con `returnValue != 0` e una con SOAP fault

### `/run-tests`

**File:** `.claude/commands/run-tests.md`

**Trigger:** esecuzione della suite di test con report.

**Workflow automatizzato:**
1. Esegue `pytest tests/ --tb=short -q --cov=src/hanel_warehouse_gateway --cov-report=term-missing`
2. Mostra i test falliti con contesto
3. Mostra la coverage per modulo
4. Segnala se la coverage scende sotto la soglia configurata (80%)

## Conseguenze

- I workflow di sviluppo ripetitivi sono eseguibili con un singolo comando
- La consistenza tra operazioni è garantita dal fatto che `/new-operation` usa sempre lo stesso schema
- I comandi sono testo — possono essere aggiornati se cambia il workflow
