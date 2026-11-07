# UC-289 — Il powerbank spegne il relay quando consuma troppo poco?

**Stato:** proposta documentale del **7 novembre 2026**. Nessuna implementazione, test software o misura fisica eseguiti. **Difficoltà: medio-alta.** PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema concreto e novità

Una scheda LoRa alimentata con powerbank può funzionare durante l'invio iniziale ma rimanere spenta dopo una lunga fase di basso consumo: *alcuni* powerbank disattivano l'uscita USB sotto una soglia di carico. Non possiamo dare per certo che succeda sulle schede o sui powerbank in uso. Il difetto sarebbe particolarmente insidioso in un relay **store-and-forward**: il nodo potrebbe aver accettato una capsula e poi non essere disponibile al contatto successivo. **L'assenza di messaggi non prova lo spegnimento dell'uscita**, che va osservato separatamente.

**Scenario Messina:** due checkpoint scolastici autorizzati a Rometta e Venetico consegnano capsule fittizie a un relay di prova alimentato da powerbank. Prima solo banco fermo; poi eventuali relay volontari degli studenti durante spostamenti ordinari, **senza tracciarli**. Nessun contatto fisico o radio è garantito dalla localizzazione ipotetica.

## Attori e utilità PollicinoNet

Docente, custode di laboratorio, 2 schede radio RX/TX di riferimento, relay portatile, logger USB *indipendente* se disponibile, collector e successivamente volontari. PollicinoNet può recuperare in differita le ricevute di custodia e i log. **Il caso misura se la sorgente resta realmente attiva in attesa di contatti futuri**, requisito diverso da durata della batteria o rumore RF.

## Bearer e contratti

- **LoRa:** annunci e capsule di test di dimensione *già supportata*, non interventi al PHY o al MAC.
- **BLE:** diagnostica e scambio locale delle ricevute, solo se l'adapter esistente lo consente.
- **Wi-Fi/LAN/Internet:** log completi e confronti non in radio.
- **USB/SD/trasporto fisico:** acquisizione indipendente dell'alimentazione e trasporto differito dei report.

Schema di fixture: `campaign_id`, `session_id`, `supply_class`, `powerbank_mode` (normale/low-current se esistente), `firmware_hash`, `radio_config_hash`, `planned_idle_window`, `current_observed?`, `usb_output_voltage_observed?`, `power_lost_at?`, `board_boot_epoch?`, `tx_confirmed?`, `rx_observed?`, `app_accepted?`, `log_completeness`, `source=SIMULATED|OBSERVED`.

Stati ammessi: `POWER_PRESENT_OBSERVED`, `USB_OUTPUT_OFF_OBSERVED`, `BOARD_UNRESPONSIVE_CAUSE_UNKNOWN`, `SERVICE_RECOVERED`, `NOT_TESTED`. Non inferire automaticamente una soglia minima di corrente o la causa da un LED.

## Prove software immediate — da implementare

1. Simulare otto sessioni con seed fisso, per due sorgenti USB e due modalità dichiarate, periodi idle differenti, ricevute ritardate, uno spegnimento USB **osservabile**, un crash applicativo senza spegnimento e due log incompleti.
2. Programmare un classificatore che separi **tensione USB assente misurata**, **scheda non raggiungibile per motivo ignoto**, **radio non scoperta** e **consegna applicativa completata**.
3. Verificare che una ricevuta più vecchia del riavvio non dimostri l'accettazione della nuova capsula, e che `UNKNOWN` resti tale con log incompleti.
4. Confrontare modalità USB normale e *low-current*, ove dichiarata dal modello di powerbank, senza attribuire risultati simulati a dispositivi reali; output dei test `PASS/FAIL/UNKNOWN/NOT_TESTED` e `source=SIMULATED`.

**Criteri di accettazione:** (A) nessuna diagnosi `AUTO_SHUTOFF_CONFIRMED` senza misura indipendente dell'uscita e protocollo controllato; (B) perdita radio ≠ power-off; (C) non confondere disponibilità elettrica con accettazione applicativa; (D) ricevute e custodie rimangono legate alla corretta sessione/epoch; (E) ogni statistica espone denominatore, completezza log e condizioni.

## Prove hardware necessarie, non svolte

In laboratorio, **4 schede** (almeno una TX, un relay e due ricevitori indipendenti ove disponibili), due PC e logger USB di classe appropriata. Sequenze bilanciate con alimentazione USB affidabile di controllo e powerbank compatibili; finestre idle predeterminate, stesso firmware, stesso supporto e antenna, stessa configurazione. Verificare l'eventuale modalità a basso carico *esattamente nel manuale del dispositivo*. Misurare tensione effettiva dell'uscita USB, reboot, presenza di trasmissioni confermate, ricezioni e accettazioni; riportare l'incertezza. La prova RF può risultare `INCONCLUSIVE`.

**Sicurezza:** non aprire o modificare powerbank/batterie, non usare resistenze improvvisate come carichi artificiali, non cortocircuitare, non cambiare antenna con trasmissione attiva; usare alimentazioni certificate e supervisionate. Nessuna prova fisica su minori in movimento finché il banco non è validato. Controllare normativa applicabile alla frequenza/potenza/duty-cycle dell'effettiva configurazione italiana.

## Privacy, limiti e anti-duplicazione

ID temporanei per campagna, nessuna targa, casa, GPS, orario individuale di tragitto, classifiche pubbliche o profili di studenti; volontariato revocabile. La valutazione non autorizza automaticamente un nodo come dispositivo per emergenze.

**UC-271** confronta le eventuali *differenze radio/EMI* USB versus powerbank; **UC-252** misura autonomia per giornata; **UC-286** misura readiness *dopo* un riavvio; **UC-184/253** riguardano salvataggio e recupero delle custodie. **UC-289** isola la possibile **disattivazione automatica dell'uscita USB durante il minimo carico** e distingue prova elettrica, presenza del nodo e riuscita della consegna. Riutilizza UC-206/277/178 senza inventare nuove radio.

Riferimento operativo (il comportamento varia con il modello): [Anker, *What is Trickle Charging Mode?*](https://service.anker.com/fr/article-description/What-is-Trickle-Charging-Mode) descrive modalità di alimentazione per dispositivi a basso assorbimento; **non costituisce una prova di comportamento dell'hardware PollicinoNet**.
