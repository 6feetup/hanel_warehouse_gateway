# Requirements — Lot Management Extension for `hanel_warehouse_gateway`

**Documento:** REQ-LOT-001  
**Versione:** 1.0  
**Data:** 2026-05-13  
**Fonte Hanel:** T-SERVER-5 — *Lean-Lift Descrizione tecnica Controllo a microprocessore MP 14-S / MP 100D-5 / Rotomat* (rev. 12.05.2023)

---

## 1. Contesto e Motivazione

Il modulo `hanel_warehouse_gateway` nella sua versione attuale utilizza esclusivamente le operazioni SOAP **V01** del t-Server Hanel, che non supportano la gestione lotti. La documentazione Hanel descrive versioni successive (**V02, V03, V04**) di alcune operazioni, pensate appositamente per il modulo ausiliario **Gestione lotti** del t-Server.

Il presente documento specifica i requisiti per estendere il gateway in modo da supportare la tracciabilità per lotto su tutti i flussi dove la documentazione Hanel prevede questa funzionalità.

> **Precondizione hardware/firmware:** la Gestione lotti deve essere attivata come modulo ausiliario nel controllo MP del magazzino verticale Hanel (impostazione lato macchina, fuori scope del gateway).

---

## 2. Mapping Operazioni V01 → Versioni con Lot Support

La tabella seguente riporta per ogni operazione V01 attualmente usata nel gateway la corrispondente versione che supporta la gestione lotti, il tipo SOAP e il tipo oggetto dati coinvolto.

| Operazione attuale (V01) | Sostituto con Lot Support | Tipo messaggio input | Tipo messaggio output | Tipo oggetto dati |
|---|---|---|---|---|
| `sendAPDReqV01` *(register_article)* | **`sendAPDReqV03`** | `SendAPDReqV03` | `SendAPDResV03` | `APDTypeV03` |
| `sendJobsReqV01` *(send_movement_order)* | **`sendJobsV02`** | `SendJobsReqV02` | `SendJobsResV02` | `JobPositionTypeV02` |
| `readAllJobsReqV01` mode=1 *(get_completed_movements)* | **`readAllJobsV02`** mode=1 | `ReadAllJobsReqV02` | `ReadAllJobsResV02` | `JobTypeV02` |
| `readAllJobsReqV01` mode=0 *(get_all_orders)* | **`readAllJobsV02`** mode=0 | `ReadAllJobsReqV02` | `ReadAllJobsResV02` | `JobTypeV02` |
| `readAllAMDReqV01` *(get_inventory)* | **`readAllAMDV04`** | `ReadAllAMDReqV04` | `ReadAllAMDResV04` | `AMDTypeV02` |
| `deleteJobReqV01` *(cancel_order)* | Invariato | `deleteJobReqV01` | `deleteJobResV01` | — |

> **Nota:** `cancel_order` non richiede variazioni perché `deleteJobV01` non ha una versione specifica per lotti — il numero ordine è sufficiente e la cancellazione non comporta movimentazione di stock.

---

## 3. Nuovi Tipi Dati SOAP (oggetti V02)

### 3.1 `AMDTypeV02` — Record dati base articolo (con lotti)

Estende `AMDTypeV01` con il campo lotto. Utilizzato da:
- `readAllAMDV04` (lettura inventario)

Differenza rispetto a `AMDTypeV01`: aggiunta del campo `batchNumber` per identificare la giacenza lotto-specifica. Un articolo con più lotti appare in record multipli (uno per lotto), ciascuno con la propria quantità per locazione fisica.

**Regola di distinzione record speciali (invariata rispetto a V01):**
- Record pool articolo: `liftNumber = 0`
- Record posti liberi: `articleNumber = " "` e `fifo = 0`

### 3.2 `JobPositionTypeV02` — Posizione ordine (con lotti)

Estende `JobPositionTypeV01` (usato in `sendJobsV01`) con il campo lotto per le posizioni di prelievo/carico. Utilizzato da `sendJobsV02`.

Il campo lotto nella posizione ordine indica a Hanel **quale lotto specifico movimentare**. Se non specificato (campo vuoto/omesso), Hanel seleziona autonomamente il lotto secondo le proprie regole interne (es. FIFO).

### 3.3 `JobTypeV02` — Record ordine (con lotti)

Estende `JobTypeV01` (usato in `readAllJobsV01`) con il campo lotto nelle posizioni restituite. Utilizzato da `readAllJobsV02` e `readJobV02`.

Nella risposta, il campo lotto per ciascuna posizione indica il lotto effettivamente movimentato dal magazzino.

---

## 4. Requisiti per Metodo Pubblico

### 4.1 `register_article` — Anagrafica articolo

**Operazione SOAP attuale:** `sendAPDReqV01`  
**Operazione SOAP target:** `sendAPDReqV03`

**Cambiamenti richiesti:**

- REQ-LOT-01: Il metodo deve accettare un parametro opzionale `batch_number: str | None = None` per associare il record di pool articolo a un lotto specifico.
- REQ-LOT-02: Se `lot_management_enabled=True`, il gateway deve invocare `sendAPDReqV03` usando `APDTypeV03` anziché `sendAPDReqV01`.
- REQ-LOT-03: Se `lot_management_enabled=False`, il comportamento deve essere identico all'implementazione attuale (retrocompatibilità garantita).
- REQ-LOT-04: La lunghezza massima di `batch_number` deve essere validata coerentemente con i vincoli di campo del t-Server (max 40 caratteri alfanumerici — da confermare dai WSDL).
- REQ-LOT-05: Il campo `batch_number` deve essere incluso nel log strutturato a livello `INFO` quando valorizzato.

**Comportamento atteso lato t-Server:** un articolo con più lotti fisici genererà record multipli in inventario, uno per lotto per locazione.

---

### 4.2 `send_movement_order` — Invio ordine di movimentazione

**Operazione SOAP attuale:** `sendJobsReqV01` → tipo `JobPositionTypeV01`  
**Operazione SOAP target:** `sendJobsV02` (SOAP: `SendJobsReqV02`) → tipo `JobPositionTypeV02`

**Cambiamenti richiesti:**

- REQ-LOT-06: `MovementLine` deve essere esteso con il campo opzionale `batch_number: str | None = None`.
- REQ-LOT-07: Se almeno una `MovementLine` dell'ordine ha `batch_number` valorizzato, il gateway deve usare `sendJobsV02` con `JobPositionTypeV02`.
- REQ-LOT-08: Se nessuna `MovementLine` ha `batch_number` valorizzato, il gateway può continuare ad usare `sendJobsReqV01` (retrocompatibilità) oppure usare sempre `sendJobsV02` con campo lotto vuoto — scelta da definire in fase di implementazione (preferibile sempre V02 per uniformità).
- REQ-LOT-09: Il campo `batch_number` in `MovementLine` è opzionale: un ordine misto (alcune righe con lotto, altre senza) deve essere supportato.
- REQ-LOT-10: Il comportamento del test mode (`test_prefix` sul `job_number`) rimane invariato e si applica anche a `sendJobsV02`.
- REQ-LOT-11: La semantica del campo lotto lato Hanel: se `batch_number` è specificato, Hanel movimenterà esclusivamente quel lotto; se omesso, Hanel selezionerà il lotto autonomamente (FIFO o regola configurata lato macchina).

---

### 4.3 `get_completed_movements` e `get_all_orders` — Lettura ordini

**Operazione SOAP attuale:** `readAllJobsReqV01` (mode=1 / mode=0) → tipo `JobTypeV01`  
**Operazione SOAP target:** `readAllJobsV02` (mode=1 / mode=0) → tipo `JobTypeV02`

**Cambiamenti richiesti:**

- REQ-LOT-12: `MovementLineResult` deve essere esteso con il campo `batch_number: str | None`.
- REQ-LOT-13: Il campo `batch_number` in `MovementLineResult` contiene il lotto **effettivamente movimentato** dal magazzino (non necessariamente quello richiesto, se non era stato specificato).
- REQ-LOT-14: Se il t-Server non restituisce il campo lotto (lotto non gestito per quell'articolo o campo assente nella risposta), `batch_number` deve essere `None`.
- REQ-LOT-15: Il calling system è responsabile della riconciliazione tra `batch_number` richiesto (in `MovementLine`) e `batch_number` restituito (in `MovementLineResult`).
- REQ-LOT-16: Entrambi i metodi (`get_completed_movements` e `get_all_orders`) devono usare `readAllJobsV02` anziché `readAllJobsReqV01`, per garantire che le informazioni di lotto siano sempre disponibili quando il modulo ausiliario è attivo.

---

### 4.4 `get_inventory` — Interrogazione giacenze

**Operazione SOAP attuale:** `readAllAMDReqV01` → tipo `AMDTypeV01`  
**Operazione SOAP target:** `readAllAMDV04` → tipo `AMDTypeV02`

**Cambiamenti richiesti:**

- REQ-LOT-17: `StockRecord` deve essere esteso con il campo `batch_number: str | None`.
- REQ-LOT-18: Per articoli gestiti a lotti, la risposta conterrà record multipli per lo stesso `article_number`, uno per ogni combinazione (lotto × locazione fisica). La somma delle `inventory_at_storage_location` per stesso `article_number` e stesso `batch_number` rappresenta la giacenza totale di quel lotto.
- REQ-LOT-19: Per articoli **non** gestiti a lotti, `batch_number` deve essere `None` (retrocompatibilità).

---

### 4.5 `cancel_order` — Cancellazione ordine

**Nessuna modifica richiesta.** `deleteJobV01` non ha versione V02 nella documentazione Hanel e la cancellazione per numero ordine non coinvolge la gestione lotti.

---

## 5. Modifiche ai Dataclass

```python
@dataclass
class MovementLine:
    article_number: str
    operation: str            # '+' = load, '-' = pick
    nominal_quantity: int     # > 0; i valori frazionari sono rifiutati all'invio
    batch_number: str | None = None   # NUOVO — opzionale

@dataclass
class MovementLineResult:
    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int      # 0=pending, 1=completed
    batch_number: str | None = None   # NUOVO — lotto effettivamente movimentato

@dataclass
class MovementResult:
    job_number: str
    job_priority: int
    job_status: int           # 0=queued, 1=in progress, 2=partial, 3=completed
    job_date: str             # formato DDMMYY
    job_time: str             # formato HHMM
    positions: list[MovementLineResult]
    # Nessuna modifica — i campi lotto sono nella struttura positions

@dataclass
class StockRecord:
    article_number: str
    article_name: str
    lift_number: int
    shelf_number: int
    compartment_number: int
    compartment_depth_number: int
    container_size: int
    fifo: int
    inventory_at_storage_location: float
    minimum_inventory: float
    batch_number: str | None = None   # NUOVO — None se articolo non gestito a lotti
```

---

## 6. Modifiche alla Configurazione

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `lot_management_enabled` | `bool` | `False` | Se `True`, il gateway usa le operazioni V02/V03/V04 per tutti i flussi che supportano lotti. Se `False`, comportamento identico alla versione attuale. |

> **Rationale del flag `lot_management_enabled`:** permette di attivare/disattivare la gestione lotti senza modifiche al codice, e consente il deploy su installazioni Hanel prive del modulo ausiliario senza errori. Quando il flag è `False`, tutti i campi `batch_number` nei dataclass sono sempre `None`.

---

## 7. Modifiche alle Operazioni SOAP — Envelope di Riferimento

### 7.1 `sendJobsV02` (send_movement_order con lotti)

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:sendJobsV02>
      <main:param>
        <xsd:job>
          <xsd:jobNumber>{job_number}</xsd:jobNumber>
          <xsd:JobPosition>
            <xsd:articleNumber>{article_number}</xsd:articleNumber>
            <xsd:operation>{operation}</xsd:operation>
            <xsd:nominalQuantity>{nominal_quantity}</xsd:nominalQuantity>
            <xsd:batchNumber>{batch_number}</xsd:batchNumber>  <!-- opzionale: omettere se None -->
          </xsd:JobPosition>
          <!-- repeat xsd:JobPosition per ogni riga -->
        </xsd:job>
      </main:param>
    </main:sendJobsV02>
  </soapenv:Body>
</soapenv:Envelope>
```

> **Da verificare:** il nome esatto del tag `batchNumber` e il namespace di appartenenza (`xsd:` o `main:`) devono essere confermati dai WSDL del t-Server o da test diretti, in quanto le tabelle dei campi del documento Hanel risultano parzialmente non estratte nella conversione PDF disponibile.

### 7.2 `readAllJobsV02` (get_completed_movements / get_all_orders con lotti)

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:readAllJobsV02>
      <main:param>
        <xsd:mode>{0|1}</xsd:mode>
      </main:param>
    </main:readAllJobsV02>
  </soapenv:Body>
</soapenv:Envelope>
```

### 7.3 `readAllAMDV04` (get_inventory con lotti)

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de">
  <soapenv:Header/>
  <soapenv:Body>
    <main:readAllAMDV04/>
  </soapenv:Body>
</soapenv:Envelope>
```

### 7.4 `sendAPDReqV03` (register_article con lotti)

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:sendAPDReqV03>
      <main:param>
        <xsd:articlePoolDataRecord>
          <xsd:articleNumber>{article_number}</xsd:articleNumber>
          <xsd:articleName>{article_name}</xsd:articleName>
          <xsd:batchNumber>{batch_number}</xsd:batchNumber>  <!-- opzionale: omettere se None -->
        </xsd:articlePoolDataRecord>
      </main:param>
    </main:sendAPDReqV03>
  </soapenv:Body>
</soapenv:Envelope>
```

---

## 8. Modifiche al Dispatcher Interno

Il dispatcher deve essere esteso per gestire il routing condizionale basato su `lot_management_enabled`:

```
# lot_management_enabled = False (comportamento attuale)
register_article(...)         → sendAPDReqV01
send_movement_order(...)      → sendJobsReqV01
get_completed_movements()     → readAllJobsReqV01 (mode=1)
get_all_orders()              → readAllJobsReqV01 (mode=0)
get_inventory()               → readAllAMDReqV01
cancel_order(...)             → deleteJobReqV01

# lot_management_enabled = True (nuovo comportamento)
register_article(...)         → sendAPDReqV03
send_movement_order(...)      → sendJobsV02
get_completed_movements()     → readAllJobsV02 (mode=1)
get_all_orders()              → readAllJobsV02 (mode=0)
get_inventory()               → readAllAMDV04
cancel_order(...)             → deleteJobReqV01  (invariato)
```

---

## 9. Gestione degli Errori — Integrazioni

Nessuna nuova categoria di errore è introdotta. Le eccezioni esistenti si applicano invariate. Aggiungere:

- REQ-LOT-21: Se `lot_management_enabled=True` e il t-Server restituisce un errore applicativo (`HanelGatewayApplicationError`) che segnala il modulo ausiliario Gestione lotti non attivo, il messaggio di errore deve includere un'indicazione esplicita che il parametro `lot_management_enabled` potrebbe richiedere disattivazione.
- REQ-LOT-22: Il campo `batch_number` non deve essere incluso nel log quando è `None`, per evitare rumore nei log di impianti senza gestione lotti.

---

## 10. Vincoli di Implementazione

- REQ-LOT-23: **Retrocompatibilità obbligatoria.** Con `lot_management_enabled=False` (default), il comportamento del gateway deve essere identico alla versione pre-lot. Nessuna firma pubblica deve essere breaking change.
- REQ-LOT-24: **Envelope XML costruiti manualmente.** Non si introducono librerie SOAP aggiuntive. Il campo `batchNumber` viene aggiunto direttamente alla costruzione XML esistente, con omissione condizionale del tag se il valore è `None`.
- REQ-LOT-25: **Thread safety invariata.** Il flag `lot_management_enabled` è read-only dopo l'inizializzazione; nessuna sincronizzazione aggiuntiva è necessaria.
- REQ-LOT-26: **Verifica WSDL obbligatoria.** Prima dell'implementazione degli envelope V02/V03/V04, è necessario recuperare i WSDL del t-Server installato (disponibili via endpoint `/HanelService?wsdl` o equivalente) per verificare i nomi esatti dei tag XML dei campi lotto nei tipi `AMDTypeV02`, `JobTypeV02`, `JobPositionTypeV02`. Le tabelle dei field definitions nella documentazione PDF non risultano completamente estratte dalla conversione automatica disponibile.

---

## 11. Dipendenze e Punti Aperti

| # | Punto Aperto | Responsabile | Note |
|---|---|---|---|
| PA-01 | Verificare nomi esatti tag XML (`batchNumber`?) per `APDTypeV03`, `JobPositionTypeV02`, `JobTypeV02`, `AMDTypeV02` dai WSDL Hanel | Francesco / Saverio Caprio (Incaricotech) | Priorità alta — blocca implementazione envelope |
| PA-02 | Confermare lunghezza massima campo lotto (ipotesi: 40 char, da confermare) | Francesco / Saverio Caprio | Da verificare su doc Hanel cap. 6.8 completo |
| PA-03 | Definire la semantica applicativa in Odoo per articoli con lotto non specificato nell'ordine (Hanel sceglie il lotto autonomamente) | Vincenzo Di Rocco / Giorgio | Impatta il flusso di validazione picking in Odoo 18 |
| PA-04 | Decidere se usare sempre `sendJobsV02` per `send_movement_order` anche senza lotti (REQ-LOT-08) | Giorgio | Preferibile sempre V02 per uniformità — da confermare |

---

*Fine documento REQ-LOT-001 v1.0*
