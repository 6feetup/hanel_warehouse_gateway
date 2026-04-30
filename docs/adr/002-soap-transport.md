# ADR-002 — HTTP/SOAP transport: requests + manual XML

**Status:** Accepted

## Context

The module must communicate with the Hanel t-Server via SOAP over HTTP. A choice must be made on how to build XML envelopes and how to execute HTTP calls.

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| `zeep` | Auto-generation from WSDL, automatic parsing | Requires accessible WSDL, heavy dependency, obscures the payload |
| `suds-jurko` | Historical Python SOAP library | Abandoned, incompatible with Python 3.10+ |
| `requests` + manual XML | Full control, no additional dependencies, deterministic payload | Manual response parsing |
| `httpx` | Native async, modern | Async not required by the specification; extra dependency |

## Decision

We adopt **`requests`** for HTTP transport and **f-string templates** for building SOAP envelopes, with **`xml.etree.ElementTree`** (stdlib) for response parsing.

Main motivation: requirements §9 explicitly indicate this approach. The Hanel t-Server exposes stable, documented SOAP operations; deriving the contract from a runtime WSDL is neither necessary nor desirable.

## Implementation

### Envelope construction

Envelopes are f-strings centralised in `_xml.py`:

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

### Executing the call

`transport.py` executes:

```python
response = requests.post(
    url=config.endpoint_url,
    data=envelope.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8"},
    timeout=config.timeout_seconds,
)
```

### Response parsing

`_xml.py` uses `ElementTree` with explicit namespaces:

```python
ns = {
    "main": "http://main.jws.com.hanel.de",
    "xsd": "http://main.jws.com.hanel.de/xsd",
}
root = ET.fromstring(response.text)
return_value = root.find(".//xsd:returnValue", ns).text
```

## Consequences

- XML payload is predictable and readable in logs
- No additional dependencies beyond `requests`
- Every envelope change is directly visible in the source
- Parsing must be tested with real XML fixtures (see ADR-007)
- If the t-Server protocol changes, modifications are localised in `_xml.py`
