# UC-298 — Room GeoTopic: segnali di aule e piani diversi senza attribuire un luogo falso

**Stato:** proposta documentale, 10 novembre 2026. Non implementato; nessuna misura reale. **Difficoltà:** medio-alta (UX di ambiguità, policy, ricerca BLE e verifica sul campo). PHY LoRa congelato, MAC, driver e firmware invariati.

## Il problema e una storia concreta

Nel corridoio di una scuola a Rometta, un telefono rileva annunci di due laboratori vicini o di piani differenti. Un beacon può essere ricevuto attraverso pareti e solai. Se la UX presenta «sei nell'aula A» con certezza solo perché il segnale è più forte, uno studente potrebbe inviare un annuncio alla room sbagliata. Un manifest **autentico** non dimostra né che l'utente si trovi nella stanza né quale sia l'aula più vicina.

**Storia:** «Voglio vedere le room candidate del mio edificio, sapere quando la stanza è incerta e scegliere esplicitamente quella giusta prima di un messaggio; non voglio essere localizzato né iscritto automaticamente».

## Attori, nodi, motivazione PollicinoNet

Due checkpoint/beacon di aula autorizzati, un client fornito dalla scuola, gestore GeoTopic, eventuale moderatore, cache e 4–6 relay LoRa volontari. Scenario di prova: due aule sullo stesso piano e una sul piano sovrastante, dapprima in laboratorio controllato; in seguito confronto fra due sedi autorizzate a Rometta e Venetico. Le schede LoRa **non sono sensori di posizione**: possono trasportare in differita il manifest pubblico della room o la sua revoca, non localizzare gli utenti.

Lo **store-and-forward** permette di aggiornare con ritardo le informazioni delle room. Il client separa chiaramente *scoperta dell'annuncio*, *validazione dell'identità della room*, *selezione del destinatario* e *permesso di pubblicare*.

## Bearer e contratto

- **BLE:** solo hint di beacon/room se i telefoni e gateway supportano BLE; RSSI come osservazione diagnostica, **mai** prova di aula o diritto di accesso.
- **LoRa:** soli riferimenti brevi/epoch di manifest pubblici nei limiti dell'adapter esistente e del budget radio; non si assume BLE sulla scheda LoRa.
- **Wi-Fi/LAN/Internet:** recupero autorizzato di manifest e messaggi completi; nessun obbligo di Internet.
- **USB/QR/trasporto fisico:** import di manifest firmati in un checkpoint scolastico disconnesso.

Oggetto proposto: `RoomSuggestion={candidate_room_id,place_label_public,issuer,manifest_hash,epoch,validation: VERIFIED|UNKNOWN|INVALID,position_confidence: NOT_ESTABLISHED,source: BLE|MANUAL|CACHED,selected_by_user: bool,reason?}`. Non rappresentare la stanza come verificata dalla sola intensità del segnale. Una scelta esplicita non conferisce privilegi di lettura o scrittura: verificare separatamente le capability della room (UC-295).

## Prova software immediata

Simulare **3 room, 2 piani, 2 beacon, 3 cache, 6 relay**, aggiornamenti di manifest e 20 scansioni fittizie con RSSI sovrapposti. Testare stessa room annunciata da più beacon, room diversa con nome uguale, beacon autentico ricevuto dall'aula accanto, un beacon non verificato, scansione vuota, ordine di ricezione invertito, manifest scaduto e revoca tardiva. Confrontare `AUTO_STRONGEST` (baseline intenzionalmente insicura) con `SHOW_CANDIDATES_CONFIRM` (proposta).

**Accettazione osservabile:** in tutti i fixture ambigui non esiste pubblicazione automatica; i destinatari coincidono esattamente con la scelta dell'utente e con una policy valida; nessuna room vicina riceve un messaggio per errore; stato UNKNOWN esplicito senza evidenza. Misurare falsi suggerimenti *simulati*, tap necessari, byte e notifiche errate; non presentare queste misure come accuratezza indoor fisica.

## Esperimento fisico indispensabile

Due beacon BLE configurabili e uno smartphone/PC scolastico; opzionalmente quattro schede LoRa e gateway esterno compatibile per i manifest. Posizionare beacon **solo in spazi autorizzati**, ripetere scansioni con operatore nei tre punti noti (non registrare chi lo porta), confrontare frequenze di ambiguità e la correttezza della **selezione manuale**, non stimare distanze da RSSI. Misurare versione OS, hardware, esito di validazione e consegna alla room applicativa; esiti UNKNOWN quando non verificabili. Una rete interscolastica con relay studenteschi è un passo successivo, non una misura già avvenuta.

## Privacy, sicurezza, differenza dai casi precedenti

Non raccogliere MAC permanenti, coordinate o frequenza di passaggio degli studenti; niente scansione passiva di persone, identificativi di partecipanti o mappe di presenza. Consenso, dati sintetici, log a retention breve, solo room pubbliche autorizzate. UC-255 verifica autenticità del beacon **senza provare presenza**; UC-247 tratta vita delle room temporanee; UC-295 tratta guest post a room **già selezionate**. **UC-298 definisce l'UX e l'invariante anti-selezione errata quando due room autentiche sono entrambe rilevabili.**

## Fonti di contesto, non risultati delle nostre schede

- Juniper, linee guida di collocazione AP/BLE per servizi di localizzazione: https://www.juniper.net/documentation/us/en/software/mist/location-services/topics/concept/mist-loc-svc-ap-placement-guidelines.html
- Repository: [UC-255](uc-255-authenticated-venue-beacon-geotopic-offline-discovery.md), [UC-295](uc-295-geotopic-nearby-rooms-guest-post-fanout.md).
