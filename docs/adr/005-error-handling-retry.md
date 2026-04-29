# ADR-005 — Gestione errori e strategia di retry

**Status:** Accettato

## Contesto

Il modulo interagisce con un sistema esterno (t-Server Hanel) soggetto a errori di rete, errori HTTP, fault SOAP e codici applicativi di errore. La specifica §5 definisce la gerarchia di eccezioni e le regole di retry. Questo ADR formalizza le scelte implementative.

## Decisione

### Gerarchia di eccezioni

```python
class HanelGatewayError(Exception):
    """Base exception. Tutti gli errori del modulo ereditano da questa."""
    def __init__(self, message: str, operation: str, detail: str, timestamp: str): ...

class HanelGatewayNetworkError(HanelGatewayError):
    """Errore di rete dopo esaurimento di tutti i tentativi di retry."""

class HanelGatewayHttpError(HanelGatewayError):
    """Risposta HTTP con status code non 2xx. Nessun retry."""
    def __init__(self, …, http_status: int): ...

class HanelGatewaySoapFaultError(HanelGatewayError):
    """Fault SOAP presente nell'envelope di risposta. Nessun retry."""
    def __init__(self, …, fault_string: str, fault_code: str): ...

class HanelGatewayApplicationError(HanelGatewayError):
    """returnValue != 0 nella risposta. Nessun retry."""
    def __init__(self, …, return_value: int): ...

class HanelGatewayValidationError(HanelGatewayError):
    """Input non valido rilevato prima dell'invio. Nessuna chiamata HTTP."""
    def __init__(self, …, field: str, value: str): ...
```

Tutte le eccezioni includono: `message`, `operation`, `detail`, `timestamp` (ISO 8601).

### Strategia di retry

Il retry si applica **esclusivamente** agli errori di rete (`requests.ConnectionError`, `requests.Timeout`). Non si applica a errori HTTP, SOAP fault o errori applicativi.

Algoritmo implementato in `transport.py`:

```python
for attempt in range(1, config.retry_attempts + 1):
    try:
        response = requests.post(…)
        break
    except (requests.ConnectionError, requests.Timeout) as exc:
        if attempt == config.retry_attempts:
            raise HanelGatewayNetworkError(…) from exc
        logger.warning("Retry %d/%d per operazione %s: %s", attempt, config.retry_attempts, operation, exc)
        time.sleep(config.retry_delay_seconds)
```

### Classificazione errori HTTP

Dopo una risposta HTTP ricevuta:
- Status 200 → prosegue con parsing XML
- Status 4xx/5xx → `HanelGatewayHttpError` immediato, nessun retry

### Rilevamento SOAP Fault

Il parsing XML verifica la presenza del tag `<soapenv:Fault>` prima di cercare il `returnValue`. Se presente: `HanelGatewaySoapFaultError`.

### Codici applicativi

`returnValue == 0` → successo.
`returnValue != 0` → `HanelGatewayApplicationError` con il valore raw e il messaggio di risposta. Il modulo non interpreta né mappa i codici di errore Hanel (la documentazione non li elenca; vedere §5.4 dei requisiti).

## Conseguenze

- Il chiamante può intercettare `HanelGatewayError` per gestire tutti gli errori in modo uniforme, oppure le sottoclassi per gestione differenziata
- La finestra di attesa massima è `retry_attempts * retry_delay_seconds` secondi
- Il `returnValue` raw è sempre incluso nell'eccezione per facilitare la diagnosi futura
