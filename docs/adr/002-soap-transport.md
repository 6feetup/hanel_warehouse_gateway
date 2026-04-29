# ADR-002 — Trasporto HTTP/SOAP: requests + XML manuale

**Status:** Accettato

## Contesto

Il modulo deve comunicare con il t-Server Hanel tramite SOAP su HTTP. È necessario scegliere come costruire gli envelope XML e come eseguire le chiamate HTTP.

## Opzioni valutate

| Opzione | Pro | Contro |
|---|---|---|
| `zeep` | Auto-generazione da WSDL, parsing automatico | Richiede WSDL accessibile, dipendenza pesante, oscura il payload |
| `suds-jurko` | Storico per SOAP Python | Abbandonato, incompatibile con Python 3.10+ |
| `requests` + XML manuale | Controllo totale, zero dipendenze aggiuntive, payload deterministico | Parsing manuale della risposta |
| `httpx` | Async nativo, moderno | Async non richiesto dalla specifica; dipendenza extra |

## Decisione

Adottiamo **`requests`** per il trasporto HTTP e **f-string template** per la costruzione degli envelope SOAP, con **`xml.etree.ElementTree`** (stdlib) per il parsing delle risposte.

Motivazione principale: i requisiti §9 indicano esplicitamente questo approccio. Il t-Server Hanel espone operazioni SOAP stabili e documentate; non è necessario né desiderabile derivare il contratto da un WSDL runtime.

## Implementazione

### Costruzione envelope

Gli envelope sono f-string centralizzati in `_xml.py`:

```python
ENVELOPE_SEND_APD = """\
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="{ns_main}"
                  xmlns:xsd="{ns_xsd}">
  <soapenv:Header/>
  <soapenv:Body>
    <main:sendAPDReqV01>
      <main:param>
        <xsd:articlePoolDataRecord>
          <xsd:articleNumber>{article_number}</xsd:articleNumber>
          <xsd:articleName>{article_name}</xsd:articleName>
        </xsd:articlePoolDataRecord>
      </main:param>
    </main:sendAPDReqV01>
  </soapenv:Body>
</soapenv:Envelope>"""
```

### Esecuzione chiamata

`transport.py` esegue:

```python
response = requests.post(
    url=config.endpoint_url,
    data=envelope.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8"},
    timeout=config.timeout_seconds,
)
```

### Parsing risposta

`_xml.py` usa `ElementTree` con namespace espliciti:

```python
ns = {
    "main": "http://main.jws.com.hanel.de",
    "xsd": "http://main.jws.com.hanel.de/xsd",
}
root = ET.fromstring(response.text)
return_value = root.find(".//xsd:returnValue", ns).text
```

## Conseguenze

- Payload XML predicibile e leggibile nei log
- Nessuna dipendenza aggiuntiva oltre `requests`
- Ogni modifica agli envelope è visibile direttamente nel sorgente
- Il parsing deve essere testato con fixture XML reali (vedere ADR-007)
- In caso di cambiamenti al protocollo t-Server, le modifiche sono localizzate in `_xml.py`
