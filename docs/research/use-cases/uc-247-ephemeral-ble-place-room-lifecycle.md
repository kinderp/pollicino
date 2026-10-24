# UC-247 — Micro-room BLE temporanee collegate a luoghi fisici

**Stato:** nuova proposta del 24 ottobre 2026; non implementata. **Difficoltà:** alta (discovery, identità, privacy, convergenza offline).

## Problema concreto
Alla fila di un cinema o durante un laboratorio al Parco Corolla alcuni dispositivi vicini desiderano creare una room temporanea sul tema `film` o `robotica`. Un altro gruppo si trova nello stesso edificio, ma **non deve essere aggregato automaticamente** alla medesima conversazione. La room nasce da un incontro BLE, ha un topic e una descrizione del luogo: può scadere, cambiare amministratore o sovrapporsi ad altre room. Il segnale BLE da solo non dimostra la presenza fisica né il diritto d'accesso.

## Attori, nodi e scenario messinese
Organizzatore volontario, partecipanti opt-in, telefono/gateway con BLE, cache del luogo e 4–8 schede LoRa studentesche come relay. Demo prima nel laboratorio, poi fra checkpoint autorizzati a Rometta, Venetico e Messina. Nessun rilevamento passivo di sconosciuti.

## Perché PollicinoNet
La presenza simultanea non è garantita: i partecipanti si incontrano, ricevono solo annunci, si separano e possono scambiare successivamente messaggi firmati via relay **store-and-forward**. L'applicazione delle room mantiene la semantica di topic, ambito pubblico, permessi, validità e conflitti; il trasporto non decide chi è nella stanza.

## Bearer
- **BLE:** annunci effimeri e inviti volontari a corto raggio; nessuna raccolta sistematica di beacon individuali.
- **LoRa:** annunci compatti di room pubbliche consentite, rinnovi e revoche, *solo* in conformità con il budget radio.
- **Wi-Fi / Internet:** inventari, messaggi, allegati e sincronizzazione delle versioni.
- **USB / trasporto fisico:** replica volontaria e firmata di piccoli manifest fra isole scolastiche.

## Contratto minimo
`room_id` opaco casuale; `topic`; `place_anchor` pubblico e grossolano oppure ID di postazione autorizzata; `scope` (pubblico/invito); `created_at`, `expires_at`, `epoch`, `owner_key`, `policy_hash`; stato `OPEN`/`CLOSED`/`EXPIRED`/`CONFLICT`. L'accesso per invito richiede capability con scadenza e anti-replay. ID pseudonimi ruotabili; nessuna rubrica o posizione personale obbligatoria. **RSSI, nome di dispositivo e GPS non sono prove di autorizzazione.**

## Test subito, solo software
Sei nodi virtuali in due aree, due topic, creazioni simultanee con stesso nome, beacon falsificati, chiusura tardiva, scadenza con orologi imprecisi, riunione dopo partizione, inviti revocati e duplicati. Accettazione: room con stesso nome ma ID distinti non si fondono; i messaggi non oltrepassano una room privata; una room scaduta è segnata incerta se l'orologio non è affidabile; aggiornamenti di epoch vecchi non riaprono una room chiusa; nessuna posizione personale compare nei log del relay.

## Prove fisiche e misure
Due telefoni/PC BLE e 4–8 schede LoRa **solo se il modello in uso supporta i bearer richiesti**. Iniziare su tavoli separati con incontri controllati; misurare discovery, falsi contatti, successo dei trasferimenti e revoche viste, non dedurre distanze esatte dal BLE. Poi checkpoint autorizzati nella provincia di Messina. TX/RX e latenza app vanno misurati con log indipendenti. Nessun dato fisico acquisito.

## Privacy e sicurezza
Partecipazione esplicita, niente tracciamento di minori né associazione stabile dispositivo–persona, rate limit sugli annunci, impostazioni di visibilità, anti-spoof e moderazione (UC-239). Il luogo di una micro-room non deve pubblicare in tempo reale la posizione di chi vi partecipa.

## Anti-duplicati
UC-083 tratta topic; UC-142 checkpoint fisici; UC-236 stanze territoriali basate su area/topic; UC-156 membership sicura. **UC-247 affronta specificamente nascita, identità, scadenza e conflitti di room create per prossimità BLE senza confondere prossimità e autorizzazione.**
