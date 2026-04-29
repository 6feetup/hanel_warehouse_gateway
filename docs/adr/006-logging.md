# ADR-006 — Strategia di logging

**Status:** Accettato

## Contesto

Il modulo deve produrre log strutturati a tutti i livelli (trasporto, operazioni, interfaccia pubblica) come da §6 dei requisiti. È una libreria Python: le scelte di logging devono rispettare le best practice per librerie (non forzare configurazione sull'applicazione chiamante).

## Opzioni valutate

| Opzione | Pro | Contro |
|---|---|---|
| `logging` stdlib | Zero dipendenze, configurabile dal chiamante, standard Python | Formato JSON richiede formatter custom |
| `structlog` | Log JSON nativi, contesto annidato, molto potente | Dipendenza esterna, overhead per questo use case |
| `loguru` | API semplice, output colorato | Dipendenza esterna, comportamento diverso da stdlib |

## Decisione

Adottiamo **`logging` stdlib**. Il modulo usa un singolo logger con nome `hanel_warehouse_gateway` e non aggiunge nessun handler di default.

## Regole implementative

### Logger

```python
import logging
logger = logging.getLogger("hanel_warehouse_gateway")
```

Ogni sotto-modulo usa lo stesso logger (non sotto-logger per modulo) per semplicità.

### Livello

Il livello del logger è impostato in `GatewayConfig.from_dict()` in base a `config["log_level"]`:

```python
logger.setLevel(getattr(logging, config.log_level, logging.INFO))
```

### Nessun handler di default

Le librerie Python non devono aggiungere handler. Il chiamante è responsabile della configurazione degli handler. Per evitare il messaggio "No handlers could be found", si aggiunge un `NullHandler`:

```python
logging.getLogger("hanel_warehouse_gateway").addHandler(logging.NullHandler())
```

Questo va in `src/hanel_warehouse_gateway/__init__.py`.

### Formato degli eventi

I log includono sempre: `operation`, `duration_ms` (dove applicabile), `message`. Non si usa un formatter custom; il formato è delegato al chiamante.

### Payload SOAP

I payload XML (envelope in uscita e risposta in entrata) sono loggati **solo se**:
- `config.log_soap_payloads = True`
- Il livello effettivo del logger è `DEBUG`

```python
if config.log_soap_payloads:
    logger.debug("SOAP request [%s]: %s", operation, envelope)
```

## Eventi obbligatori

| Evento | Livello | Dove |
|---|---|---|
| Chiamata SOAP avviata (operazione + params non sensibili) | `INFO` | `operations.py` |
| Esito positivo (operazione + durata ms) | `INFO` | `operations.py` |
| Retry in corso (tentativo N di M, motivo) | `WARNING` | `transport.py` |
| Failure finale (tipo, operazione, dettaglio) | `ERROR` | `transport.py` / `operations.py` |
| Envelope XML in uscita | `DEBUG` (solo se `log_soap_payloads`) | `transport.py` |
| Envelope XML in entrata | `DEBUG` (solo se `log_soap_payloads`) | `transport.py` |

## Conseguenze

- Il chiamante configura handler, formatter e destinazione dei log senza modificare il modulo
- I payload SOAP sono disabilitati per default (contengono dati di magazzino potenzialmente sensibili)
- Aggiungere `structlog` in futuro non rompe l'interfaccia: basta sostituire il logger interno
