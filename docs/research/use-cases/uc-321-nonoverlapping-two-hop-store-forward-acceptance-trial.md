# UC-321 — Consegna A→B→C con due contatti non sovrapposti: prova end-to-end

**Stato:** proposta documentale del 18 novembre 2026. Nessun simulatore, test radio, protocollo o risultato fisico dichiarato. **Difficoltà:** media nel simulatore, medio-alta nel banco e alta nell'estensione geografica.

## Il problema concreto
Vogliamo dimostrare il funzionamento essenziale di una rete opportunistica: una richiesta parte dalla scuola A; il relay B la memorizza durante un primo contatto; solo **dopo che il primo contatto è terminato** B incontra il destinatario C e lo inoltra. A e C non sono mai collegati simultaneamente nello scenario di prova. Senza una traccia verificabile, una consegna ottenuta per Wi-Fi/Internet nascosto o con tre nodi sempre raggiungibili può sembrare una prova di store-and-forward senza esserlo.

Storia didattica: «Come docente voglio poter mostrare ai ragazzi una consegna differita realmente completata in due finestre disgiunte, distinguendo la custodia sul relay dall'accettazione nell'applicazione destinataria».

## Attori e modello messinese
Nodi A (lab di origine), B (scheda/courier studente **volontario**), C (lab destinatario), PC di log A e C, osservatore con orologio di riferimento e due collector, eventualmente cache di backup. In laboratorio A/B/C sono **ruoli**, non vere distanze. Un'estensione potrà usare due checkpoint autorizzati ad esempio fra Rometta e Venetico, con relay itinerante che svolge normali spostamenti, **senza** acquisire traiettorie personali. Non presumere radio LoRa fra comuni.

## Perché PollicinoNet e quali bearer
Il principio è custodire un oggetto esatto oltre la fine del contatto, non costruire un percorso radio continuo. **LoRa** trasferisce solo una capsula piccola e supportata; **BLE** può essere usato nel vicino se disponibile; **Wi-Fi/Internet** serve per log e oggetti voluminosi ma va DISABILITATO come percorso alternativo durante la prova di consegna LoRa; **USB/SSD/trasporto fisico** è un braccio sperimentale distinto, mai attribuito alla radio.

Schema: `TwoWindowTrial={trial_id,object_hash,adapter_profile,window_ab_start_stop,window_bc_start_stop,forbidden_ac=true,tx_observed,rx_observed,b_persisted_receipt,c_app_accept_receipt,missing_log_flags,bearer_per_hop,clock_uncertainty}`. Richiedere `end(AB) < start(BC)` tenendo conto dell'incertezza degli orologi. Se ciò non è dimostrabile: `INCONCLUSIVE`.

## Software subito (test ancora da eseguire)
Simulare 3 nodi, 12 capsule sintetiche, due finestre volutamente separate; poi prove negative:
1. contatto B-C prima del completamento di A-B;
2. B spento o riavviato tra i contatti, con e senza persistenza;
3. A-C accidentalmente abilitato, con conseguente invalidazione del braccio;
4. duplicati, TTL scaduto, hash alterato, app C che rifiuta un oggetto pur ricevuto;
5. ACK di B confuso con accettazione C e log di un hop mancanti.

Metriche: numero di capsule effettivamente accettate in C, ritardo applicativo (con incertezza), byte per bearer, prove complete/inconcludenti, copie duplicate respinte; mai «PDR reale» da simulazione.

## Hardware necessario e protocollo
**Fase 1:** tre schede LoRa e due PC, più ricevitori/loggers indipendenti quando disponibili. Creare **finestre applicative** AB e BC comandate e loggate (più sicuro che manipolare radio o disturbare link esistenti), impedire un percorso Internet/LAN nascosto, verificare hash delle capsule e ricevute firmate dove disponibile. Provare sia scheda B sempre alimentata sia spegnimento controllato fra le finestre, verificando prima limiti flash e recupero sicuro. **Fase 2:** checkpoint scolastici autorizzati e relay mobili volontari; raccogliere solo log aggregati di sessione, non percorsi né cronologia delle presenze. Non pubblicare percentuali di consegna prima di campioni reali con denominatori e condizioni.

## Sicurezza, privacy e distinzione
Materiale sintetico, nonce/id di prova che scadono, consenso revocabile, nessun ID personale persistente, nessun GPS o cronologia degli spostamenti; contro replay, messaggi falsificati e ricevute non firmate, separare accettazione e custodia. Attivare quote per evitare congestione; rispettare limiti radio applicabili.

**Anti-duplicati:** UC-001 descrive il **servizio** di ferry della conoscenza, UC-097 la **gestione delle campagne**, UC-221 la **ricevuta applicativa**, UC-300 la **rimozione del ponte**, UC-195 l'**attribuzione dei ritardi**. UC-321 definisce una **prova minima falsificabile a due finestre disgiunte**, necessaria prima di affermare che il sistema ha dimostrato una consegna store-and-forward reale. Il PHY LoRa congelato non cambia.
