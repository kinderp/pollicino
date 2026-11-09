# UC-295 — GeoTopic: scrivere alle room vicine senza entrarci

**Stato:** proposta documentale del **9 novembre 2026**, non implementata o testata. **Difficoltà:** alta (autorizzazione, scelta contestuale, fan-out, privacy e riconciliazione). Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema e scenario concreto

Una persona entra in un laboratorio scolastico autorizzato a Rometta, oppure si trova presso un punto pubblico di Venetico. Il client può proporre più **room territoriali o tematiche** rilevanti (es. «laboratorio robotica», «scambio libri», «segnalazioni didattiche»). La persona vuole inviare **una richiesta di disponibilità di un componente o di un libro** a una o più room, senza dover effettuare iscrizioni permanenti e senza condividere l'itinerario. Se scrive «cerco un caricatore», deve poter scegliere **esattamente quali room riceveranno il messaggio**; nessuna app deve replicarlo automaticamente in room vicine non selezionate.

**Story:** «Vedo le room proposte vicino a me, scelgo a quali rivolgere un messaggio una tantum e posso ricevere una risposta nel canale previsto senza aderire stabilmente a nessuna stanza».

## Attori, nodi e ruolo PollicinoNet

Client volontario, proprietari/moderatori delle room, checkpoint scolastici autenticati, cache di prossimità, 4–8 relay degli studenti store-and-forward, destinatari che consulteranno in seguito le room. Il mittente e i destinatari **non devono essere contemporaneamente connessi**. Lo strato applicativo decide permessi, room destinatarie e visibilità; il trasporto opportunistico conserva e inoltra **soltanto le capsule autorizzate**.

La prossimità radio o un geofence sono **indizi per suggerire** room, non prova di posizione, appartenenza, ruolo o diritto a pubblicare. Si possono offrire scelta manuale, suggerimento indoor tramite beacon di sede autenticato (UC-255), oppure per outdoor una zona pubblica grossolana scelta volontariamente dall'utente; un GNSS opzionale resta locale e non va nei relay.

## Bearer e confini di responsabilità

- **BLE:** annuncio volontario del checkpoint/room hint e recupero locale di piccoli manifest; nessuna scansione identificativa dei compagni.
- **LoRa:** solo ID/epoch/digest compatti autorizzati di room pubbliche, avvisi di disponibilità e, *se già supportato dall'adapter*, piccolissimi stati; **mai presupporre che il testo del post possa viaggiare su LoRa**.
- **Wi-Fi/LAN/Internet:** manifest completi, contenuti dei post, policy e ricevute, con Internet opzionale.
- **USB, QR o trasporto fisico:** manifest autorizzati e oggetti cifrati per le sedi isolate; BLE/Wi-Fi per sincronizzare i contenuti quando possibile.

## Contratto applicativo proposto

`RoomCandidate = {room_id, place_id?, topic_id, issuer, manifest_hash, epoch, expires_at, guest_policy, confidence: VERIFIED_VENUE|UNVERIFIED_HINT|MANUAL, status: CURRENT|STALE|UNKNOWN}`.

`GuestIntent = {intent_id:random, chosen_room_ids[], preview_hash, per_room_capabilities[], expiry, max_posts, optional_return_mailbox, consent_timestamp_local}`.

`RoomDelivery = {intent_id, room_id, policy_epoch, per_room_envelope_hash, disposition: PENDING|MODERATED|ACCEPTED|REJECTED|EXPIRED|UNKNOWN, receipt_ref?}`.

Ogni room riceve un envelope indipendente e minimizzato. Un'intenzione inviata a due room non crea automaticamente membership, una subscription (UC-083) o accesso alle risposte riservate. Una *capability guest* firmata, limitata all'azione e valida per la room specifica, autorizza il tentativo di pubblicazione, non la pubblicazione garantita. Moderazione e revoche possono arrivare in differita; le risposte devono utilizzare una mailbox o capability di risposta limitata (UC-257), non un recapito personale in chiaro.

## Cosa testare subito in software

1. Simulare **4 room, 2 luoghi fittizi, 3 cache e 6 relay**. Alcune room si sovrappongono; una è solo su invito; due hanno lo stesso nome visibile, ma ID diversi.
2. Mostrare tre modalità di scoperta: scelta manuale, hint BLE autenticato, zona pubblica grossolana outdoor. Il client segnala `UNKNOWN` quando non può verificare un luogo e **non pubblica silenziosamente**.
3. Utente senza membership seleziona esattamente due room. Iniettare manifest scaduti, consenso negato, guest capability mancante, revoca, duplicati, perdita di Internet e messaggi ricevuti in ordine diverso.
4. Verificare che `(intent_id, room_id)` sia idempotente; doppia consegna non crea doppio post, nessuna room non selezionata riceve contenuti, non avviene iscrizione implicita e `guest_policy=DENY` blocca.
5. Registrare esiti e metriche `SIMULATED`: selezione esplicita, falsi instradamenti, accettazioni, bytes/contatto, tempi alla ricevuta, messaggi scartati e numero di dati personali nel relay (obiettivo zero).

**Gate di accettazione:** nessun invio senza selezione esplicita e autorizzazione valida, zero contaminazioni tra room nei casi artificiali, nessun cambio implicito di membership e stato `UNKNOWN` preservato se mancano prove. Test non eseguiti.

## Prove fisiche necessarie

Due checkpoint scolastici autorizzati (Rometta/Venetico), 2 smartphone o PC BLE compatibili, 4–8 schede LoRa e due computer per i log. Prima ripetere una discovery di room su banco e un guest post tramite BLE/Wi-Fi; poi far arrivare soltanto un piccolo annuncio/receipt fra relay LoRa **quando l'adapter applicativo lo consente**. Misurare TX effettive, RX, accettazione della pubblicazione e tempi. Non dedurre raggio, aula precisa o presenza di una persona dal segnale; non serve spostarsi o tracciare studenti.

## Privacy e differenza rispetto ai precedenti

Opt-in, interruttore di STOP (UC-217), rate limit, antispam, moderazione (UC-239), firma manifest (UC-255), capability per room, cifratura dei post privati, scadenze e minimizzazione delle ricevute. Un relay non ottiene identità, classe o traiettoria del mittente.

**UC-236** definisce selezione topic+zona, **UC-247** creazione/vita delle micro-room BLE, **UC-255** autenticità degli annunci, **UC-257** risposta privata a un post, **UC-083** subscription. **UC-295 riguarda la diversa operazione utente: pubblicazione una tantum a un insieme esplicito di room vicine, anche senza membership, con fan-out e permessi verificabili.**