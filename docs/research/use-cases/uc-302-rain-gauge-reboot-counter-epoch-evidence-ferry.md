# UC-302 — Pluviometri scolastici: conteggio di pioggia affidabile dopo riavvii, reset e consegne tardive

**Stato (11 novembre 2026):** nuovo scenario IoT didattico documentato; nessun codice/test eseguito, nessuna misura ambientale reale. **Difficoltà: media-alta.** PHY LoRa congelato invariato.

## Problema concreto

Un pluviometro a vaschetta basculante registra impulsi e spesso trasmette un **conteggio cumulativo**. Se il logger si riavvia, il contatore riparte da zero, cambia epoca o può andare in overflow; inoltre i pacchetti possono arrivare duplicati o fuori ordine. Sottrarre semplicemente due numeri ricevuti può produrre pioggia negativa, doppio conteggio o intensità inventate.

**Scenario Messina:** tre stazioni didattiche *fisse e autorizzate* nell'area Rometta–Venetico–Spadafora producono dati sintetici di pioggia raccolti con relay LoRa. Non si deve inferire rischio alluvione, frane, allerta meteo o sicurezza dei luoghi dal prototipo.

## Attori e perché PollicinoNet

Sensore a impulsi o generatore di impulsi innocuo, logger, scheda LoRa, relay studenti facoltativi, checkpoint e docente che rivede i dati. La rete tollera disconnessioni e consegna i piccoli aggiornamenti in ritardo; conservare `station_id`, **epoca del contatore** e sequenza consente di ricostruire solo incrementi supportati da evidenza.

La fonte di riferimento Mesonet descrive i tipping bucket come contatori di impulsi con cumulati periodicamente resettati e segnala limitazioni fisiche a pioggia debole e intensa: https://www.mesonet.org/about/instruments . **Nessun valore o accuratezza di Mesonet è assunto per sensori scolastici.**

## Bearer

- **LoRa:** solo piccoli record applicativi `(station_pseudonym, counter_epoch, seq, count, timestamp_quality, schema_id)` se compatibili con il PHY/adapter attuali.
- **BLE:** diagnostica o piccolo delta locale, se disponibile.
- **Wi-Fi/Internet:** esportazioni complete e analisi, non presupposti.
- **USB/SD / trasporto fisico:** log originali o campioni per verifica indipendente; distinguere chiaramente il trasporto dalla radio.

## Contratto dati

`RainTipObservation={station_id_pseudonymous, logger_boot_epoch, monotonic_seq, cumulative_tip_count, counter_bits?, reset_reason?, sensor_calibration_id, observation_interval, clock_quality, schema_version, signature_or_auth_tag?}`.

Il `cumulative_tip_count` non è una misura di millimetri se manca una calibrazione nota; dichiarare `UNKNOWN` per conversione o intervallo indeterminato. Un reset autenticato può autorizzare un nuovo conteggio, non ricostruisce gli impulsi persi. Le conversioni da impulsi a precipitazione sono solo indicative e soggette ai limiti del sensore.

## Esperimento software senza hardware

Tre sensori fittizi, **48 ore** sintetiche, **60 impulsi** prefissati, sei cambi epoca/riavvio, un rollover di un contatore piccolo di prova, perdita di pacchetti, ricevute duplicate, consegne tardive e orologi non sincronizzati. Confrontare il naïf `last_received_count - previous_count` con un aggregatore che usa epoca, sequenza e intervalli validi. Produrre la ricostruzione con etichette `EXACT_FROM_LOG`, `LOWER_BOUND`, `UNKNOWN`, non inserire zeri dove mancano impulsi.

**Accettazione:** (1) duplicati con stessa epoca/seq non incrementano il cumulato; (2) un reset non crea precipitazione negativa; (3) un presunto rollover è accettato solo se il formato/ampiezza del contatore e la continuità sono dimostrati; (4) se mancano log o epoche non si produce un totale certo; (5) una correzione tardiva conserva provenienza e revisione, non sovrascrive silenziosamente.

**Metriche:** falsi incrementi/doppie somme, intervalli conclusivi vs ignoti, byte di controllo, quota ricostruita da un log locale originale, ritardo di disponibilità delle osservazioni. Risultati solo come `SIMULATED` finché non vengono raccolti dati veri.

## Prove fisiche

Fase A (banco): **1 generatore manuale di impulsi o sensore didattico, 2 PC e 3–4 schede**, con disconnessioni e riavvii controllati, ripetendo un numero *noto e indipendentemente contato* di impulsi. Niente acqua necessaria. Fase B: 2–3 pluviometri adeguatamente installati in punti autorizzati, con registrazione locale indipendente, protocollo di manutenzione, controllo dei falsi impulsi e calibrazione; 4–6 schede e due checkpoint. Non aspettarsi che le schede abbiano già un ingresso sensore o l'app di conteggio: verificare prima le capability.

## Privacy e sicurezza

Solo sensori meteorologici presso postazioni fisse approvate, no proprietà/abitazioni private o deduzioni su routine personali; autenticare la provenienza, versionare la calibrazione, conservare il minimo di metadati. Lo studente non deve uscire durante temporali né entrare in zone a rischio. Non collegare l'output a sistemi operativi di allerta o protezione civile. Dati scaduti e mancanti restano visibilmente incompleti.

## Anti-duplicazione

UC-003 distribuisce sensori rurali; UC-031 tratta la calibrazione; UC-131 recupera segmenti mancanti; UC-253 protegge custodia su flash; UC-171 verifica dati di qualità delle acque. **UC-302 verifica la semantica *del contatore cumulativo di impulsi* fra epoche di riavvio/overflow e notifiche in ritardo:** un dato può essere ben consegnato e restare scientificamente scorretto se il contatore è stato interpretato male.
