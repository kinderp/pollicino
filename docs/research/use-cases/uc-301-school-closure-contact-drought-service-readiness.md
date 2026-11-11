# UC-301 — Rete LoRa scolastica: continuità di servizio durante chiusure e giorni senza contatti

**Stato (11 novembre 2026):** proposta documentale, nessun simulatore eseguito e nessuna misura fisica effettuata. **Difficoltà: medio-alta.** PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema concreto

Un bundle didattico arriva durante una normale giornata scolastica grazie ai contatti occasionali con relay volontari. Ma nel fine settimana, durante una chiusura o nel pomeriggio, i contatti possono diventare molto più rari. Un contenuto urgente *per una lezione* può scadere prima che un nodo torni disponibile; una cache fissa potrebbe anche riempirsi nell'attesa. Non è corretto attribuire l'assenza di contatti a una mancanza degli studenti.

**Scenario Messina:** modellare checkpoint autorizzati chiamati `Rometta`, `Venetico`, `Spadafora` e `Villafranca`; nodi fissi in scuole e relay volontari operano con disponibilità variabile. Nessuna copertura LoRa fra questi luoghi è presupposta. La prima prova avviene interamente in un laboratorio.

**Domanda osservabile:** con le *stesse richieste e scadenze*, quale quota di oggetti risulta ricevuta dall'app entro la deadline se è presente una lunga finestra senza relay? Quanto spazio di custodia serve? Quali contenuti devono essere preparati *prima* della chiusura?

## Attori e ruolo di PollicinoNet

Docente e amministratore del testbed, due o più checkpoint fissi, 4–8 schede LoRa di prova, PC/collector e relay studenti esclusivamente volontari. PollicinoNet è adatto perché custodisce oggetti e li inoltra quando ricompare un contatto, anche se sorgente e destinatario non sono contemporaneamente disponibili. Il calendario descrive **disponibilità di infrastrutture**, non la presenza delle persone; la previsione non costituisce prova del contatto.

- **DISCOVERY:** annuncio compatto di disponibilità e classe di contenuto; non contiene nomi degli studenti.
- **EXACT:** hash/manifest dell'oggetto e ricevuta dell'applicazione.
- **SEMANTIC:** tipo `lesson-pack`, `science-data`, `maintenance`, senza inferenze sulla persona.

## Bearer

- **LoRa:** capsule e digest/identificatori compatti *già supportati* dall'adapter e nel budget radio; non trasferire PDF grandi.
- **BLE:** handoff locale dove i dispositivi lo supportano.
- **Wi-Fi/LAN/Internet:** manifest completi, log e oggetti voluminosi quando autorizzati.
- **USB/SSD / trasporto fisico:** cache e file nei contatti volontari; contabilizzare separatamente questo trasporto.

## Test software immediato

Simulare **8 nodi**, **24 bundle** artificiali, due checkpoint fissi e finestre di contatto sintetiche riferite a 7 giorni. Confrontare tre bracci a parità di workload: `WEEKDAY_BASELINE`, `CLOSURE_CONTACT_DROUGHT`, `PREFETCH_BEFORE_CLOSURE`. Introdurre chiusura di 48 ore *inventata*, capienza 32/64/128 KiB, TTL/scadenze diverse, duplicati, contatti di durata insufficiente, carenza energetica e ricevute mancanti. Nessun calendario dei singoli studenti.

**Metriche:** numero di `app_receipt` verificati entro deadline / denominatore noto, tempo all'accettazione applicativa, occupazione massima cache, blocchi scaduti, oggetti non dimostrabilmente consegnati. Non dichiarare PDR radio su queste tracce.

**Criteri di accettazione:** (1) uno stop volontario elimina solo una disponibilità *simulata*, non genera colpa o punteggi; (2) una promessa di contatto non vale come consegna; (3) con log mancanti l'esito è `UNKNOWN`, non `FAIL`; (4) prefetch conta come riuscito solo con oggetto esatto verificato prima della scadenza; (5) il prefetch non supera quote, autorizzazioni e custodia disponibili.

Esempio di record: `{campaign_id, arm, epoch, checkpoint_id_coarse, workload_hash, contact_window_class, bundle_id, deadline, app_receipt_id?, buffer_capacity, log_complete, used_bearer}`. Non includere percorsi o orari individuali.

## Prova hardware indispensabile

Prima **4–6 schede e 2 PC nello stesso laboratorio**, con finestre di disponibilità applicativa programmate e un checkpoint spento *solo* come parte di una prova autorizzata; ripetere i bracci in ordine alternato senza cambiare il PHY. Per simulare 48 ore non è necessario che gli studenti trasportino la scheda per 48 ore. Rilevare code, accettazioni e tempi effettivi. Solo dopo il collaudo predisporre due checkpoint scolastici reali e campagne volontarie, senza dipendere dall'ordinario tragitto casa–scuola.

Per affermare continuità reale servono campioni ripetuti di contatti, RX osservabili, ricevute `EXACT`, budget energetico, log completi e verifica delle regole radio. Una simulazione di 48 ore non misura autonomia, copertura o affidabilità provinciale.

## Privacy, sicurezza e confini

Niente rilevazione delle presenze o dei tragitti; solo calendario **pubblico/organizzativo** e ID temporanei per campagna; opt-out immediato, niente pressione sulle famiglie, conservazione breve dei log. Non utilizzare per reperibilità o avvisi reali di protezione civile. Cifratura dei bundle riservati, autorizzazioni e quote locali.

## Anti-duplicazione

UC-025 pianifica contatti ricorrenti e routing, UC-224 valuta la calibrazione delle probabilità di contatto, UC-300 rimuove un *singolo ponte*. **UC-301 testa il vuoto di servizio prevedibile di intere finestre scolastiche (sera, chiusura, fine settimana), le scadenze applicative e il preposizionamento prima del vuoto**, senza tracciare volontari.

Riferimento architetturale (non affermazione di conformità PollicinoNet): RFC 9171, store-carry-forward e opportunità intermittenti: https://www.rfc-editor.org/rfc/rfc9171.html
