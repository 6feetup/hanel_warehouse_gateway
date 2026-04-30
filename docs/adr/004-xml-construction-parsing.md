# ADR-004 — XML construction and parsing

**Status:** Accepted

## Context

The module must build SOAP XML envelopes for 6 distinct operations and parse their responses. An approach that is maintainable, testable, and free of external dependencies is required.

## Options evaluated

### Envelope construction

| Option | Pros | Cons |
|---|---|---|
| f-string template | Readable, predictable output, easily testable | Manual escaping required if data contains special XML characters |
| `xml.etree.ElementTree` builder | Automatic safe escaping | Verbose, less readable for complex envelopes |
| `lxml` | Powerful API, schema validation | External C dependency, not needed |
| Jinja2 template | Separation of template from code | External dependency, overhead |

### Response parsing

| Option | Pros | Cons |
|---|---|---|
| `xml.etree.ElementTree` stdlib | Zero dependencies, sufficient for simple structures | Non-intuitive API for namespaces |
| `lxml` | Powerful XPath, better namespace handling | External C dependency |
| `xmltodict` | Dict-friendly | External dependency, loses XML structure |

## Decision

**Construction:** f-string templates in `_xml.py`, with mandatory escaping of user values via a helper function `_xml_escape(value: str) -> str` that replaces `&`, `<`, `>`, `"`, `'`.

**Parsing:** `xml.etree.ElementTree` stdlib with explicit namespaces passed as a dict to `find()` / `findall()` calls.

## Organisation of `_xml.py`

```
_xml.py
├── Template constants (ENVELOPE_*)
├── _xml_escape(value) → str
├── build_*(…) → str          # one function per operation
└── parse_*(xml_text) → dict  # one function per operation
```

Each `build_X` / `parse_X` pair corresponds to a SOAP operation.

## Special character handling

Values inserted into envelopes (`article_number`, `article_name`, `job_number`) are passed through `_xml_escape` before interpolation. This prevents XML injection and ensures that payloads containing characters such as `&` or `<` do not produce malformed envelopes.

## Namespace handling in responses

t-Server responses use the namespaces `http://main.jws.com.hanel.de` and `http://main.jws.com.hanel.de/xsd`. The namespace dict is defined as a constant in `_xml.py` and reused across all `parse_*` functions.

## Consequences

- XML templates are visible and editable without knowledge of a builder API
- Tests verify the exact output of envelopes (see ADR-007)
- XML response fixtures (`tests/fixtures/*.xml`) are the reference data for parsers
- If the t-Server changes its XML structure, modifications are isolated in `_xml.py`
