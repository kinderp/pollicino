# UC-262 — Capsule piccole ricomposte via LoRa con budget applicativo verificabile

**Stato:** proposta documentale del 29 ottobre 2026; nessun codice, test o risultato radio eseguito. **Difficoltà:** medio-alta (prototipo), alta (campagna radio). Il PHY LoRa congelato, MAC, driver e firmware restano invariati.

## Problema risolto e storia

Un laboratorio di Rometta vuole consegnare a Venetico una piccola scheda informativa firmata, più grande del *payload applicativo effettivamente supportato* dal bearer LoRa esistente ma troppo piccola per giustificare sempre un handoff BLE/Wi-Fi. Con relay intermittenti, alcuni frammenti arrivano duplicati, fuori ordine o dopo un riavvio. Dobbiamo sapere **se e quando** il destinatario ricostruisce e accetta esattamente la capsula, evitando di saturare la radio per un beneficio marginale.

**User story:** come docente voglio confrontare la consegna di un oggetto di prova tramite pochi frammenti applicativi, un eventuale invio intero quando ammesso, e il rinvio a un bearer ricco, con budget di traffico esplicito e ricevuta finale verificabile.

## Attori e perché PollicinoNet

Publisher scolastico, 4–8 schede relay store-and-forward, due checkpoint fissi autorizzati, destinatario e collector indipendente. PollicinoNet separa `DISCOVERY` (ID e disponibilità), `EXACT` (hash dell'oggetto completo e manifest) e `SEMANTIC` (tipo e priorità, mai prova d'integrità). La fragmentazione non autorizza mai a considerare consegnato un oggetto parziale.

**Limite esplicito:** non presupponiamo che il firmware/adapter oggi esponga già tutte le operazioni per inviare/ricevere frammenti. Prima della prova radio si verifica la *capability reale* dell'interfaccia applicativa; se manca, il test rimane software finché non esiste un adattatore compatibile, senza modificare il PHY congelato. Non si afferma di implementare automaticamente BPv7.

## Bearer

- **LoRa:** soltanto identificativi, richieste e microframmenti che rientrano nel limite payload e nel budget applicativo/regolamentare verificati; mai file voluminosi.
- **BLE:** fallback per ottenere schemi/manifest e capsule quando è disponibile.
- **Wi-Fi/LAN/Internet:** confronto con un bearer ricco, recupero dell'oggetto completo e raccolta dei log.
- **USB/SD/trasporto fisico:** backup e trasferimento esatto offline; gli studenti possono spostare copie già verificate senza registrare itinerari.

## Cosa testare subito in software

1. Interrogare o configurare uno **size cap applicativo**, calcolando l'overhead di envelope, identificativo, indice/offset, autenticazione e codifica; nessuna costante RF inventata.
2. Preparare capsule sintetiche di 64, 128, 256, 512 e 1024 byte **solo come input software**; definire ID di campagna (UC-256), ID oggetto, lunghezza totale, hash completo, fragment-index/offset e scadenza.
3. Confrontare: A) invio intero solo se consentito; B) segmentazione applicativa con numero massimo di frammenti e ritrasmissioni, senza loop; C) rifiuto `TOO_LARGE_FOR_LORA` e handoff BLE/Wi-Fi/trasporto fisico. Non assumere che B vinca.
4. Iniettare partizioni, pacchetti mancanti, duplicati, overlap incongruenti, manifest modificato, nonce ripetuto, riavvio dopo conferma di custodia (UC-253), e ripresa con inventario limitato.
5. Rifiutare i frammenti di campagna/versione sconosciuta, imporre limiti a memoria, bytes e tempo per ricomposizione, garbage collection con conservazione delle custodie valide.
6. Il destinatario firma/produce una **ricevuta di accettazione applicativa** (UC-221) *solo* dopo ricomposizione, verifica SHA-256 del contenuto esatto e validazione delle autorizzazioni.
7. Misurare **in simulazione** byte/on-wire stimati dal contratto locale, overhead relativo, copie, completamenti, TTL scadute, memoria occupata e oggetti unici accettati; marcare tutto `SIMULATED`.

**PASS software:** mai `ACCEPTED` per un oggetto incompleto o di hash errato; mai superamento del payload/budget configurato; bounded retries e memoria; stesso oggetto accettato al massimo una volta dall'applicazione.

## Prova fisica e scenario Messina

Prima 2 schede e 2 PC nello stesso laboratorio, poi 4–8 schede e postazioni scolastiche autorizzate fra Villafranca, Rometta, Venetico, Spadafora. Usare identificativi di prova, osservatori RX indipendenti, profilo radio approvato e burst **limitati**, con sessioni brevi e separate. Verificare capienza reale, TX effettivi, RX osservati, costo di handshake, fragments ricevuti, oggetti con hash corretto e ricevute al destinatario. Confrontare il costo con BLE e con il semplice rinvio: il caso può risultare **non conveniente** su LoRa.

Non dichiarare PDR, portata, throughput, airtime o energia senza misure di strumenti e denominatori verificati (UC-178/231). Prima dell'emissione verificare frequenza, potenza, sottobanda e limiti applicabili in Italia.

## Privacy, sicurezza e differenza dai casi esistenti

Capsule fittizie, ID temporanei, nessuna geolocalizzazione individuale; payload cifrati se necessario, autenticazione end-to-end, replay guard, anti-bomba di frammenti, dimensioni/retention limitate, registri accessibili solo al team didattico. Non esporre in chiaro i titoli di documenti sensibili.

UC-018 studia shard erasure-coded; UC-112 recupera **oggetti grandi via bearer ricchi**; UC-188 valuta la fattibilità di un trasferimento in un contatto; UC-249 codifica singoli microfatti tipizzati; UC-230 verifica adapter; UC-240 riduce i loop. **UC-262 misura precisamente la convenienza e la correttezza dell'eventuale ricomposizione di capsule piccole sul solo bearer LoRa, con un limite di budget e una decisione esplicita di fallback.**

**Riferimento metodologico:** RFC 9171, §§5.8–5.9, [fragmentation e reassembly](https://www.rfc-editor.org/rfc/rfc9171.html), come modello concettuale; non come dichiarazione di compatibilità implementata.
