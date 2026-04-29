# ADR-008 — Comportamento validazione campi in input

**Status:** Accettato

## Contesto

La specifica §7 stabilisce che i campi `articleNumber` e `articleName` hanno un limite di 40 caratteri alfanumerici. Il comportamento in caso di violazione è configurabile: troncamento (con warning) oppure eccezione. È necessario formalizzare il default e il meccanismo di configurazione.

## Decisione

Il comportamento **default è `raise HanelGatewayValidationError`**.

Il troncamento silente è opt-in tramite `config["validation_truncate"] = True`.

## Razionale

Un troncamento silente nasconde un problema dati nel sistema chiamante. Un'eccezione forza il chiamante ad accorgersene immediatamente. Il default conservativo è preferibile; il chiamante può scegliere il troncamento consapevolmente.

## Parametro di configurazione

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `validation_truncate` | `bool` | `False` | Se `True`, tronca a 40 chars e logga `WARNING` invece di sollevare eccezione |

Questo parametro è aggiunto a `GatewayConfig` (vedere ADR-003).

## Campi soggetti a validazione

| Campo | Limite | Operazione |
|---|---|---|
| `article_number` | max 40 chars | `register_article`, `send_movement_order`, `cancel_order` |
| `article_name` | max 40 chars | `register_article` |
| `job_number` | max 40 chars | `send_movement_order`, `cancel_order` |

## Implementazione

La validazione avviene in `operations.py` prima della costruzione dell'envelope, tramite una funzione helper:

```python
def _validate_field_length(value: str, field: str, operation: str, config: GatewayConfig) -> str:
    if len(value) <= 40:
        return value
    if config.validation_truncate:
        logger.warning("Campo '%s' troncato a 40 chars in operazione '%s'", field, operation)
        return value[:40]
    raise HanelGatewayValidationError(
        message=f"Campo '{field}' supera il limite di 40 caratteri",
        operation=operation,
        detail=f"Lunghezza: {len(value)}, valore: {value!r}",
        timestamp=datetime.utcnow().isoformat(),
        field=field,
        value=value,
    )
```

## Conseguenze

- Per default, dati troppo lunghi producono un'eccezione immediata e tracciabile
- Il chiamante che preferisce il troncamento deve dichiararlo esplicitamente nella configurazione
- In modalità troncamento il log `WARNING` garantisce tracciabilità anche senza eccezione
