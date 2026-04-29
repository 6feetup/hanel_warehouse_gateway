# ADR-003 — Gestione configurazione

**Status:** Accettato

## Contesto

Il modulo deve essere configurabile senza modifiche al codice. L'interfaccia pubblica accetta un `dict` come da §2 dei requisiti. Internamente è necessario validare e normalizzare i parametri in modo robusto.

## Classificazione dei parametri

I parametri sono divisi in tre categorie con origine distinta:

| Categoria | Parametri | Origine |
|---|---|---|
| **Volatili / ambiente** | `endpoint_url`, `test_mode`, `test_prefix` | Variabile d'ambiente (`.env`) |
| **Secret** | *(credenziali future, es. API key, password)* | Variabile d'ambiente (`.env`) |
| **Statici / strutturali** | tutti gli altri | Dict passato dal chiamante o valori di default |

I parametri volatili e i secret non devono mai essere hardcoded nel codice sorgente o in file committati. Vengono letti da variabili d'ambiente, che in sviluppo sono caricate da un file `.env` (non committato).

## Opzioni valutate

| Opzione | Pro | Contro |
|---|---|---|
| Plain `dict` | Zero overhead | Nessuna validazione, nessun type checking, errori silenziosi |
| `pydantic.BaseModel` | Validazione potente, coercizione tipi, errori chiari | Dipendenza esterna non necessaria |
| `dataclasses` stdlib + `__post_init__` | Validazione esplicita, zero dipendenze, type hints nativi | Coercizione manuale dei tipi |
| `TypedDict` | Type hints senza overhead runtime | Nessuna validazione runtime |

## Decisione

Adottiamo un **`@dataclass` `GatewayConfig`** (stdlib) con validazione in `__post_init__`. L'interfaccia pubblica `HanelWarehouseGateway(config: dict)` converte il dict in `GatewayConfig` all'inizializzazione.

I parametri volatili e i secret vengono letti da variabili d'ambiente tramite **`python-dotenv`**, che carica automaticamente il file `.env` alla radice del progetto se presente. `python-dotenv` è l'unica dipendenza esterna aggiuntiva consentita oltre a `requests`.

## Parametri

```python
@dataclass
class GatewayConfig:
    endpoint_url: str
    namespace_main: str = "http://main.jws.com.hanel.de"
    namespace_xsd: str = "http://main.jws.com.hanel.de/xsd"
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    test_mode: bool = False
    test_prefix: str = "TEST_"
    log_level: str = "INFO"
    log_soap_payloads: bool = False
    validation_truncate: bool = False  # vedi ADR-008
```

Il parametro `validation_truncate` è aggiunto rispetto ai requisiti originali (vedi ADR-008).

## Comportamento di validazione

`__post_init__` verifica:
- `endpoint_url` non vuoto e inizia con `http://` o `https://`
- `timeout_seconds` > 0
- `retry_attempts` >= 1
- `retry_delay_seconds` >= 0
- `log_level` è uno tra `DEBUG`, `INFO`, `WARNING`, `ERROR`

Gli errori di configurazione sollevano `ValueError` con messaggio esplicito (non `HanelGatewayValidationError`, che è riservato alla validazione dei dati di business pre-invio).

## File .env

In sviluppo, i parametri volatili e i secret sono definiti in un file `.env` alla radice del progetto:

```dotenv
# .env — NON committare questo file
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
# Esempio secret futuro:
# HANEL_API_KEY=...
```

Il file `.env` **non deve essere committato**. Il repository include un `.env.example` committato con valori placeholder come riferimento:

```dotenv
# .env.example — copia in .env e compila con i valori reali
HANEL_ENDPOINT_URL=http://<host>:<port>/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

Il `.gitignore` deve contenere la riga `.env`.

## Costruzione da variabili d'ambiente + dict

`GatewayConfig` offre un factory method `from_env()` che:
1. Carica il file `.env` tramite `python-dotenv` (se presente)
2. Legge le variabili d'ambiente con prefisso `HANEL_`
3. Accetta un dict opzionale per i parametri statici (override o valori aggiuntivi)
4. I valori del dict hanno precedenza sulle variabili d'ambiente

```python
@classmethod
def from_env(cls, overrides: dict | None = None) -> "GatewayConfig":
    from dotenv import load_dotenv
    load_dotenv()  # no-op se .env non esiste
    env_values = {
        "endpoint_url": os.getenv("HANEL_ENDPOINT_URL"),
        "test_mode": os.getenv("HANEL_TEST_MODE", "false").lower() == "true",
        "test_prefix": os.getenv("HANEL_TEST_PREFIX", "TEST_"),
    }
    merged = {k: v for k, v in env_values.items() if v is not None}
    if overrides:
        merged.update(overrides)
    return cls.from_dict(merged)

@classmethod
def from_dict(cls, d: dict) -> "GatewayConfig":
    known_keys = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in d.items() if k in known_keys}
    return cls(**filtered)
```

Le chiavi sconosciute vengono ignorate con un log `WARNING`, per consentire forward compatibility se il chiamante passa parametri aggiuntivi.

## Uso tipico

```python
# Sviluppo: legge da .env
client = HanelWarehouseGateway(GatewayConfig.from_env())

# Produzione: variabili d'ambiente iniettate dall'orchestratore (Docker, k8s…)
client = HanelWarehouseGateway(GatewayConfig.from_env())

# Test: override esplicito senza .env
client = HanelWarehouseGateway(GatewayConfig.from_env({
    "endpoint_url": "http://mock-server/",
    "test_mode": True,
}))
```

## Conseguenze

- `endpoint_url`, `test_mode`, `test_prefix` non compaiono mai in file committati
- I secret futuri seguono lo stesso pattern senza modifiche architetturali
- `python-dotenv` è la seconda (e ultima) dipendenza esterna di produzione consentita
- Aggiungere un parametro volatile richiede: aggiungere la variabile d'ambiente in `.env.example`, aggiornare `from_env()`, aggiornare questo ADR e `CLAUDE.md`
- Errori di configurazione emergono all'inizializzazione, non al primo utilizzo
- Il codice interno usa sempre `GatewayConfig` tipizzato, mai dict raw
