# ADR-004 — Costruzione e parsing XML

**Status:** Accettato

## Contesto

Il modulo deve costruire envelope SOAP XML per 6 operazioni distinte e parsare le relative risposte. È necessario scegliere un approccio che sia manutenibile, testabile e privo di dipendenze esterne.

## Opzioni valutate

### Costruzione envelope

| Opzione | Pro | Contro |
|---|---|---|
| f-string template | Leggibile, output predicibile, facilmente testabile | Escaping manuale se i dati contengono caratteri XML speciali |
| `xml.etree.ElementTree` builder | Safe escaping automatico | Verboso, meno leggibile per envelope complessi |
| `lxml` | API potente, validazione schema | Dipendenza C esterna, non necessaria |
| Jinja2 template | Separazione template da codice | Dipendenza esterna, overhead |

### Parsing risposta

| Opzione | Pro | Contro |
|---|---|---|
| `xml.etree.ElementTree` stdlib | Zero dipendenze, sufficiente per strutture semplici | API non intuitiva per namespace |
| `lxml` | XPath potente, namespace gestiti meglio | Dipendenza C esterna |
| `xmltodict` | Dict-friendly | Dipendenza esterna, perde struttura XML |

## Decisione

**Costruzione:** f-string template in `_xml.py`, con escape obbligatorio dei valori utente tramite una funzione helper `_xml_escape(value: str) -> str` che sostituisce `&`, `<`, `>`, `"`, `'`.

**Parsing:** `xml.etree.ElementTree` stdlib con namespace espliciti passati come dict alle chiamate `find()` / `findall()`.

## Organizzazione di `_xml.py`

```
_xml.py
├── Costanti template (ENVELOPE_*)
├── _xml_escape(value) → str
├── build_*(…) → str          # una funzione per operazione
└── parse_*(xml_text) → dict  # una funzione per operazione
```

Ogni coppia `build_X` / `parse_X` corrisponde a un'operazione SOAP.

## Gestione caratteri speciali

I valori inseriti negli envelope (`article_number`, `article_name`, `job_number`) sono passati attraverso `_xml_escape` prima dell'interpolazione. Questo previene XML injection e garantisce che payload con caratteri come `&` o `<` non producano envelope malformati.

## Gestione namespace nelle risposte

Le risposte del t-Server usano i namespace `http://main.jws.com.hanel.de` e `http://main.jws.com.hanel.de/xsd`. Il dict di namespace è definito come costante in `_xml.py` e riutilizzato in tutte le funzioni `parse_*`.

## Conseguenze

- I template XML sono visibili e modificabili senza conoscere le API di un builder
- I test verificano l'output esatto degli envelope (vedere ADR-007)
- Le fixture XML di risposta (`tests/fixtures/*.xml`) sono i dati di riferimento per i parser
- Se il t-Server cambia struttura XML, le modifiche sono isolate in `_xml.py`
