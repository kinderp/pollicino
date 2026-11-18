# UC-320 — Richiesta cartacea e ritiro di informazioni pubbliche da una cache offline

**Stato:** nuova proposta del 18 novembre 2026; prototipo e prove non eseguiti. **Difficoltà:** media per il prototipo con dati pubblici, alta per un servizio accessibile e realmente utilizzabile.

## Problema e attori
Chi non possiede uno smartphone o non vuole installare un'app dovrebbe poter richiedere un contenuto pubblico utile (una guida locale Raiatea, un orario didattico pubblicabile, una scheda culturale) e riceverlo in un punto scolastico autorizzato **anche se il documento non è ancora nella cache locale**. Il sistema non deve trasformare una semplice richiesta in registrazione o tracciamento della persona.

Attori: visitatore o docente, sportello assistito, due cache scolastiche, stampante o schermo accessibile, relay PollicinoNet volontari con schede LoRa, curatore dei contenuti pubblici. Scenario: uno sportello didattico a Venetico possiede il catalogo di guide del territorio ma non il documento richiesto, custodito in una cache scolastica di Milazzo. Un relay può trasportare la richiesta e poi riportare l'oggetto via contatti successivi; la disponibilità al ritiro è **eventuale**, non garantita.

## Perché PollicinoNet è adatto
Il bisogno di un contenuto è una richiesta piccola, il contenuto è più grande e può essere recuperato in modo asincrono. `DISCOVERY` identifica gli oggetti pubblici disponibili, `EXACT` identifica un hash/versione autorizzata e `SEMANTIC` resta una descrizione per l'utente: **sono contratti informativi, non radio**. Una ricevuta di custodia intermedia non prova disponibilità allo sportello.

## Bearer
- **Carta/QR/codice breve:** la persona seleziona o riceve un identificativo casuale di ritiro; il codice testuale deve essere alternativa reale al QR.
- **LoRa:** richieste e annunci compatti già supportati e autenticati, mai il PDF completo se non compatibile con i limiti.
- **BLE:** sincronizzazione ravvicinata opzionale fra sportello e relay.
- **Wi-Fi/Internet:** trasferimento del PDF o della scheda e aggiornamento dei contenuti quando permesso.
- **USB/SSD e trasporto fisico:** trasferimento di file voluminosi e consegna periodica da un curatore al punto di ritiro.

## Contratto e test software
Proposta: `PublicPickup={request_id_random,public_artifact_hash,source_license_revision,pickup_site_id,created_epoch,expires_at,state:REQUESTED|AVAILABLE|COLLECTED|EXPIRED|WITHDRAWN,receipt_hash}`. Il token stampato **non conferisce permessi ulteriori** e non deve contenere nomi o preferenze sensibili. L'assenza di ritiro non indica disinteresse.

Simulator Python con 3 cache, 2 sportelli e 20 richieste fittizie; introdurre duplicati, revoca della guida, disponibilità tardiva, token illeggibile, tentativi di ritiro ripetuti, contenuto di licenza mancante e fallimento stampante. Criteri: contenuto non autorizzato mai stampato, richiesta scaduta non riattivata, code sconosciute indicate come tali, `COLLECTED` solo con evento di consegna confermato (non sulla sola scansione), nessuna esposizione di richieste individuali nei log di relay.

## Hardware e messa alla prova
Iniziare con 2 PC, una stampante opzionale e 4 schede LoRa nel laboratorio, con finestre di contatto simulate e materiali interamente fittizi; misurare richieste ricostruite, errori di scansione/trascrizione, tempi di consegna e ricevute applicative. Una sperimentazione reale presso sedi diverse richiede autorizzazione del gestore, modalità assistita per chi non legge codici, verifica di licenze e ritiro presidiato. **Non promettere tempi di disponibilità.**

## Privacy, sicurezza, accessibilità e differenze
Solo materiali pubblici, niente pratiche personali, mediche, assistenziali o scolastiche riservate. Cifratura/autenticazione per i messaggi di controllo; minimizzazione di token, luoghi e metadati; token usa-e-getta solo nei limiti consentiti dalla riconciliazione offline, con stato conservativo in caso di doppio ritiro non verificabile. Nessuna pubblicazione di liste di richiedenti. Prevedere anche **codice breve leggibile e assistenza umana**: QR non può essere l'unico canale di accesso (https://www.section508.gov/blog/accessibility-bytes/qr-codes/).

**Anti-duplicati:** UC-203 fornisce il **bearer ottico**, UC-121 riconcilia **moduli**, UC-041 espone contenuti cached via hotspot e UC-316 è la **guida museale**. UC-320 tratta invece l'intero **servizio di richiesta asincrona e ritiro assistito senza smartphone**, compresi scadenza, accessibilità e autorizzazione alla consegna.

**Gate:** nessun vero sportello pubblico senza approvazione; il PHY LoRa rimane congelato.
