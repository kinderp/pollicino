# UC-334 — Checkpoint LoRa e temperatura: disponibilità reale fra sole e ombra

**Stato:** proposta documentale del 23 novembre 2026; **nessuna prova implementata o eseguita**. **Priorità:** alta per rete didattica con schede reali. **Difficoltà:** media software, medio-alta nella prova fisica controllata.

## Problema in parole semplici
Una scheda può essere accesa senza consegnare capsule all'applicazione quando cambia l'ambiente rispetto al laboratorio. Temperatura del contenitore, alimentazione, firmware, antenna e luce solare possono cambiare insieme: una mancata consegna **non dimostra una causa termica**. Si vuole verificare la *prontezza applicativa* del relay con un confronto controllato, senza surriscaldare volontariamente la scheda o batterie e senza superare i limiti dei componenti.

## Attori e scenario messinese
Docente, due postazioni fisse nel cortile scolastico autorizzato, ricevitore indipendente, 3–4 schede LoRa, due PC, termometro/logger e studenti volontari come relay store-and-forward. Rometta, Spadafora e Venetico sono possibili future sedi, **non** collegamenti intercomunali verificati. Niente GPS, tragitti degli studenti, tetti o postazioni esposte non autorizzate.

## Perché PollicinoNet e bearer
La rete distingue custodia, inoltro, ricezione RF osservabile e **ricevuta dell'applicazione**: è adatta a confrontare contatti intermittenti e prova di consegna A→B→C (UC-321). **LoRa (PHY congelato):** capsule compatte ammesse dall'adapter, mai serie complete. **BLE:** diagnostica locale se supportata. **Wi-Fi/LAN/Internet:** scarico autorizzato di log e analisi, non una scorciatoia nascosta per dichiarare riuscita la prova LoRa. **USB/SD/trasporto fisico:** log ricchi e configurazioni, con provenienza del bearer distinta.

## Schema minimo dei dati
trial_id; station_code; board_model_revision; firmware_hash; supply_type; battery_present; board_and_supply_rating_reference; enclosure_type; antenna_config; placement_class=SHADE|AMBIENT_EXPOSURE; enclosure_temperature; ambient_temperature; temperature_timestamp_quality; contact_window_id; tx_attempt_id; receiver_observation_id; app_receipt_id; reboot_marker; missing_log_reason; operator_notes. Escludere dai confronti appaiati prove con alimentazione, distanza o antenna modificate.

## Software subito — solo specifica, NON eseguito
Creare 3 condizioni sintetiche × 30 finestre × 2 postazioni, con 8 temperature mancanti, 5 reboot, 6 ricevute duplicate, 4 registri RX incompleti e 5 cambi di alimentazione. Il validatore Python dovrà distinguere TX_ATTEMPT, RX_OBSERVED, APP_ACCEPTED e UNKNOWN; deduplicare le ricevute; marcare INCONCLUDENTE un confronto senza controlli; **non attribuire automaticamente al calore le perdite**. I limiti termici sono input del datasheet del dispositivo reale, mai valori universali inventati.

## Hardware reale — non eseguito
Prima una prova indoor a temperatura ordinaria e alimentazione USB sicura, con log indipendenti. Poi confronto statico fra ombra e ambiente esterno ordinario **solo entro i limiti di ciascuna scheda, involucro e alimentatore**, su supporti consentiti; niente Li-ion esposte al sole, riscaldatori o stress termico deliberato. Ripetere con stesse posizioni e antenne, prevedere stop supervisionato, misurare timestamp e ricevute radio/app separatamente. Solo dopo prove autorizzate pianificare i checkpoint di provincia: nessuna distanza, PDR o autonomia viene assunta.

## Privacy, sicurezza e criteri
Usare codici di postazione non personali, log a conservazione breve, capsule autenticate e verifiche di integrità. Non registrare i percorsi dei minori, non attribuire comportamenti a studenti, rispettare limiti radio locali. **PASS software** se stati e confondenti sono classificati correttamente; **FAIL** se la temperatura viene dichiarata causa senza misure controllate; **UNKNOWN** se mancano riferimenti o log. Nessun risultato fisico dichiarato. Non modificare PHY LoRa, MAC, driver o firmware.

## Anti-duplicazione
UC-214 misura umidità dei box; UC-218 il carico termico durante inferenza edge AI; UC-223 il microclima sole/ombra; UC-252 la giornata energetica, UC-286 il cold-start, UC-289 il powerbank a basso carico, UC-313 attività multi-radio. **Qui l'esito è la disponibilità end-to-end applicativa di un relay LoRa al variare di condizioni termiche ordinarie**, controllando fattori confondenti e prove di consegna.

## Fonte tecnica
Semtech, SX1262 e datasheet del chip (non sostituisce specifiche della scheda completa o della batteria): https://www.semtech.com/products/wireless-rf/lora-connect/sx1262
