# Hanel t-Server SOAP Mock

Mock server del servizio SOAP Hanel t-Server, pensato per lo sviluppo e il testing del modulo `hanel_warehouse_gateway` senza necessità del magazzino fisico.

---

## Avvio rapido

```bash
# dalla root del progetto
docker compose up --build
```

Il server sarà raggiungibile su `http://localhost:8080/HanelService`.

---

## Configurazione

Le variabili d'ambiente possono essere impostate in `docker-compose.yml`:

| Variabile | Default | Descrizione |
|---|---|---|
| `AUTO_COMPLETE_SECONDS` | `10` | Secondi dopo i quali un ordine passa automaticamente a status=3. Impostare `0` per disabilitare. |
| `MOCK_DATA_DIR` | `/app/data` | Percorso della directory contenente i file JSON dei dati mock. |

---

## Dati mock

I dati di partenza sono definiti in tre file JSON nella directory `mock_server/data/`:

| File | Contenuto |
|---|---|
| `articles.json` | Articoli registrati nel magazzino |
| `jobs.json` | Ordini di movimento (in vari stati) |
| `inventory.json` | Livelli di stock per locazione fisica |

I file possono essere modificati liberamente. Per applicare le modifiche senza riavviare il container, chiamare `POST /admin/reset`.

### Formato `articles.json`

```json
{
  "ART-001": {"article_number": "ART-001", "article_name": "Nome articolo"}
}
```

### Formato `jobs.json`

```json
[
  {
    "job_number": "ORD-001",
    "job_priority": 1,
    "job_status": 0,
    "job_date": "290426",
    "job_time": "0800",
    "positions": [
      {
        "article_number": "ART-001",
        "operation": "+",
        "nominal_quantity": 10.0,
        "actual_quantity": 0.0,
        "container_size": 1,
        "position_status": 0
      }
    ]
  }
]
```

`job_status`: `0`=in coda, `1`=in lavorazione, `2`=parziale, `3`=completato  
`operation`: `+`=prelievo, `-`=carico  
`position_status`: `0`=pending, `1`=completato

### Formato `inventory.json`

```json
[
  {
    "article_number": "ART-001",
    "article_name": "Nome articolo",
    "lift_number": 1,
    "shelf_number": 12,
    "compartment_number": 3,
    "compartment_depth_number": 1,
    "container_size": 1,
    "fifo": 1,
    "inventory_at_storage_location": 150.0,
    "minimum_inventory": 20.0
  }
]
```

Un articolo può avere più record (più locazioni fisiche). Record con `lift_number=0` e `shelf_number=0` indicano articoli presenti nel master ma senza stock fisico.

---

## Endpoint SOAP

Tutti gli endpoint SOAP accettano richieste `POST` su `/HanelService` con `Content-Type: text/xml`.

### Registrazione articolo — `sendAPDReqV01`

```bash
curl -s -X POST http://localhost:8080/HanelService \
  -H "Content-Type: text/xml" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:main="http://main.jws.com.hanel.de"
        xmlns:xsd="http://main.jws.com.hanel.de/xsd">
    <soapenv:Header/>
    <soapenv:Body>
      <main:sendAPDReqV01>
        <main:param>
          <xsd:articlePoolDataRecord>
            <xsd:articleNumber>ART-NEW</xsd:articleNumber>
            <xsd:articleName>Nuovo Articolo</xsd:articleName>
          </xsd:articlePoolDataRecord>
        </main:param>
      </main:sendAPDReqV01>
    </soapenv:Body>
  </soapenv:Envelope>'
```

Risposta: `<xsd:returnValue>0</xsd:returnValue>`

---

### Invio ordine — `sendJobsReqV01`

```bash
curl -s -X POST http://localhost:8080/HanelService \
  -H "Content-Type: text/xml" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:main="http://main.jws.com.hanel.de"
        xmlns:xsd="http://main.jws.com.hanel.de/xsd">
    <soapenv:Header/>
    <soapenv:Body>
      <main:sendJobsReqV01>
        <main:param>
          <xsd:job>
            <xsd:jobNumber>ORD-TEST</xsd:jobNumber>
            <xsd:JobPosition>
              <xsd:articleNumber>ART-001</xsd:articleNumber>
              <xsd:operation>+</xsd:operation>
              <xsd:nominalQuantity>5.0</xsd:nominalQuantity>
            </xsd:JobPosition>
          </xsd:job>
        </main:param>
      </main:sendJobsReqV01>
    </soapenv:Body>
  </soapenv:Envelope>'
```

---

### Lettura ordini — `readAllJobsReqV01`

`mode=0` restituisce tutti gli ordini, `mode=1` solo quelli completati (status=3).

```bash
curl -s -X POST http://localhost:8080/HanelService \
  -H "Content-Type: text/xml" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:main="http://main.jws.com.hanel.de"
        xmlns:xsd="http://main.jws.com.hanel.de/xsd">
    <soapenv:Header/>
    <soapenv:Body>
      <main:readAllJobsReqV01>
        <main:param><xsd:mode>0</xsd:mode></main:param>
      </main:readAllJobsReqV01>
    </soapenv:Body>
  </soapenv:Envelope>'
```

---

### Livelli di stock — `readAllAMDReqV01`

```bash
curl -s -X POST http://localhost:8080/HanelService \
  -H "Content-Type: text/xml" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:main="http://main.jws.com.hanel.de">
    <soapenv:Header/>
    <soapenv:Body>
      <main:readAllAMDReqV01/>
    </soapenv:Body>
  </soapenv:Envelope>'
```

---

### Cancellazione ordine — `deleteJobReqV01`

Funziona solo su ordini con `job_status=0`. Restituisce `returnValue=1` se l'ordine non esiste o è già in lavorazione/completato.

```bash
curl -s -X POST http://localhost:8080/HanelService \
  -H "Content-Type: text/xml" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:main="http://main.jws.com.hanel.de"
        xmlns:xsd="http://main.jws.com.hanel.de/xsd">
    <soapenv:Header/>
    <soapenv:Body>
      <main:deleteJobReqV01>
        <main:param>
          <xsd:jobNumber>ORD-001</xsd:jobNumber>
        </main:param>
      </main:deleteJobReqV01>
    </soapenv:Body>
  </soapenv:Envelope>'
```

---

## Endpoint admin

Endpoint HTTP di supporto per il testing.

| Metodo | URL | Descrizione |
|---|---|---|
| `GET` | `/admin/state` | Dump JSON dello stato corrente (articoli, ordini, inventario) |
| `POST` | `/admin/reset` | Ripristina lo stato ai dati iniziali dai file JSON |
| `POST` | `/admin/complete-all` | Porta immediatamente tutti gli ordini pendenti a status=3 |

```bash
# Verifica stato
curl http://localhost:8080/admin/state | python3 -m json.tool

# Forza completamento ordini
curl -X POST http://localhost:8080/admin/complete-all

# Ripristina stato iniziale
curl -X POST http://localhost:8080/admin/reset
```

---

## Test automatizzati

Il progetto include una suite di test in `tests/test_mock_server.py` che richiede il server in esecuzione.

```bash
pip install pytest requests
pytest tests/test_mock_server.py -v
```

---

## Namespace SOAP

| Prefisso | Namespace |
|---|---|
| `soapenv` | `http://schemas.xmlsoap.org/soap/envelope/` |
| `main` | `http://main.jws.com.hanel.de` |
| `xsd` | `http://main.jws.com.hanel.de/xsd` |
