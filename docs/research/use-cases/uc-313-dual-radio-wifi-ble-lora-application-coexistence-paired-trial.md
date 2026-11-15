# UC-313 — Relay LoRa e attività Wi-Fi/BLE sulla stessa scheda: prova appaiata

**Stato:** proposta documentale, non implementata. **Priorità:** alta per la rete scolastica messinese. **Difficoltà:** medio-alta. **Dominio:** collaudo LoRa / bearer eterogenei.

## Problema e valore
Un checkpoint o relay portatile può essere configurato per usare LoRa e, quando l'hardware lo consente, Wi-Fi/BLE per trasferimenti più ricchi. Attivare discovery BLE, sincronizzazione o Wi-Fi potrebbe modificare il carico CPU, la pianificazione dei task, l'assorbimento o la disponibilità dell'applicazione. Se una capsula non arriva, non dobbiamo chiamarlo automaticamente "disturbo radio": la perdita potrebbe avvenire prima o dopo il ricevitore LoRa. Verifichiamo **se la consegna applicativa cambia** tra condizioni controllate. Non supponiamo che le schede disponibili supportino simultaneamente tutti i bearer.

## Scenario provincia di Messina
In un laboratorio scolastico a Rometta, una scheda relay conserva microcapsule destinate a un checkpoint presso Venetico o Spadafora. Un contatto futuro può consentire la consegna. Prima di distribuire i nodi volontari dobbiamo capire se la sincronizzazione BLE/Wi-Fi interferisca con il *servizio applicativo* LoRa del singolo dispositivo. Le località sono destinatari logici dell'esperimento: nessun collegamento radio intercomunale è già dimostrato.

## Attori, nodi e bearer
- 1 dispositivo candidato (specificare modello/revisione SoC, firmware esistente, radio e antenne); 1-2 ricevitori indipendenti LoRa; 1 smartphone/PC companion; 1 collector con log.
- **LoRa:** capsule compatte e protocollo già supportato, senza cambiare il PHY congelato.
- **BLE:** se realmente supportato, discovery e sincronizzazione locale controllata.
- **Wi-Fi/Internet:** se supportati e autorizzati, trasferimento di log o piccoli oggetti, mai assunto disponibile per default.
- **USB / trasporto fisico:** raccolta di log e dataset integrali; fallback senza collegamento.
- Contratti DISCOVERY/EXACT/SEMANTIC restano astratti, non equivalgono a bearer.

## Ipotesi e disegno sperimentale
Tre condizioni logiche: **A** LoRa con companion inattivo; **B** LoRa con attività BLE controllata; **C** LoRa con Wi-Fi autorizzato (eventuale **D** BLE+Wi-Fi solo se la board lo supporta). Ordine dei blocchi alternato A/B/C/C/B/A e condizioni appaiate. Stesse posizioni, payload, versione, alimentazione, configurazione LoRa e strumentazione. Se non è possibile attivare uno scenario con i programmi esistenti, segnalarlo "non testabile", non cambiare PHY o inventare una misura. Per gli esperimenti futuri, eventuali modifiche al solo codice applicativo necessitano review separata: questo UC non le applica.

Registro per ogni tentativo: campaign_id, case_id, board_rev, software_hash, capsule_id, scheduled_tx, **tx_observed**, rx_independent_observed, host_ingest, app_accept_receipt, timestamps con incertezza, companion_mode, power_mode, missing_log_reason. Calcolare denominatori di successo **solo** sulle TX realmente documentate; conservare a parte richieste, log mancanti e messaggi mai partiti. Rilevare anche CPU/task backlog, alimentazione e reset se osservabili, senza creare nuovi contatori fittizi.

La guida Espressif descrive la coesistenza *Wi-Fi e Bluetooth a 2,4 GHz* nei SoC compatibili; **non** costituisce prova di interferenza diretta con LoRa sub-GHz né si applica automaticamente a tutte le LILYGO: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/coexist.html

## Prova software immediata — non eseguita
Dataset sintetico deterministico: 3 scenari × 40 intenti TX, comprendendo blocchi CPU, invii non avvenuti, rx radio mancata, rx valida ma coda host satura, duplicati e assenza dei log. Script previsto: raggruppamento per capsule_id, matrice delle transizioni TX→RX→host→app, confronto delle ricevute esatte senza numeri attribuiti a prove fisiche.

**Criteri di accettazione:** (1) nessuna TX presunta da un'intenzione schedulata; (2) impossibile attribuire causalità RF da una ricevuta assente; (3) solo gli app_accept_receipt validi contano come consegne; (4) scenari non supportati marcati N/A; (5) un seed riproduce esattamente conteggi e input sintetici.

## Hardware reale e prove necessarie — non eseguite
Prima 4–6 schede e due PC in laboratorio, ricevitori indipendenti e logger corrente/riavvii se disponibili. Testare capacità effettive e alimentazione, poi esposizioni appaiate in posizione fissa e autorizzata, sotto limiti di trasmissione regolamentari. Una seconda fase può collocare checkpoint in più scuole **soltanto dopo** rilievi e autorizzazioni. Non pubblicare dati di percorsi o presenze degli studenti.

## Privacy e sicurezza
Partecipazione volontaria, nodi con pseudonimi a durata limitata, nessuna associazione tra ID radio e studente, eliminazione dei log grezzi a scadenza; Wi-Fi soltanto in rete di laboratorio e con permesso IT; niente scansioni indiscriminate di dispositivi altrui. Evitare tentativi aggressivi di carico radio. I log devono escludere payload personali.

## Anti-duplicazione
- **UC-271:** cambia la sorgente USB/powerbank, non l'attività del companion sulla stessa board.
- **UC-265:** confronta trasmettitori LoRa concorrenti, non attività Wi-Fi/BLE e scheduling applicativo del relay.
- **UC-277:** diagnostica le fasi di perdita; qui si applica quella diagnosi a una **variabile di trattamento appaiata** sul dispositivo multi-bearer.
- **UC-297/299:** riguardano smartphone in background e Wi-Fi ospiti isolato, non il comportamento della scheda LoRa sotto attività companion.

**Confini:** nessuna nuova funzione, nessuna modifica a PHY/MAC/driver/firmware, nessun risultato RSSI/PDR/airtime/energia o attribuzione causale senza misure reali.
