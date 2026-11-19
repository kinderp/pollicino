# UC-323 — Livello di una cisterna didattica: distinguere acqua vera e falso eco

**Stato (19 novembre 2026):** solo proposta di sperimentazione IoT, nessun sensore, firmware o test fisico eseguito. **Difficoltà:** media nel simulatore, medio-alta nel confronto strumentale. Nessuna modifica al PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Una piccola cisterna didattica raccoglie acqua per un orto scolastico. Un sensore a ultrasuoni misura la distanza dalla superficie; quando la superficie è increspata, il sensore è inclinato oppure produce un eco debole può comparire un dato incompatibile con il reale livello. Se la rete consegna i valori in ritardo, un grafico che ordina per arrivo può far sembrare che la cisterna si sia svuotata o riempita all'improvviso.

**Obiettivo:** ricostruire un diario della misura distinguendo «valore osservato», «lettura sospetta», «misura mancante» e «valore validato contro riferimento». Non comandare pompe o valvole né dichiarare disponibilità idrica operativa.

## Attori e scenario provinciale
Due recipienti da laboratorio a bassa tensione, un sensore di distanza per recipiente, logger, 3–4 relay LoRa scolastici, due PC/cache e un docente. Fase 1 in un banco asciutto e protetto a Milazzo; fase 2 con postazioni fisse autorizzate eventualmente a Rometta/Venetico. Il relay di uno studente può trasportare i record quando incontra un checkpoint, senza GPS né diario della sua mobilità.

## Perché PollicinoNet è adatto
Le osservazioni sono piccole e tollerano ritardi. PollicinoNet mantiene l'identità esatta della misura, la sua calibrazione e il momento dell'osservazione, anche quando le capsule passano fra cache differenti. La presenza di un record ricevuto non dimostra che il sensore abbia misurato bene.

**Schema applicativo proposto:** station_epoch, seq, observed_window, clock_quality, raw_distance, distance_unit, mounting_height, geometry_profile_hash, sensor_model, calibration_version, echo_quality_if_available, quality_flags, exact_record_hash. Stati: RAW, SUSPECT, REFERENCE_CHECKED, MISSING, UNKNOWN. Una trasformazione da distanza a volume è consentita soltanto se forma, posizione e calibrazione del recipiente sono note.

## Bearer
- **LoRa:** record di livello o avvisi minimi firmati/autenticati se contenuti nei limiti attuali del trasporto; niente flussi continui e niente promesse di copertura.
- **BLE:** acquisizione locale delle letture e controllo del logger.
- **Wi-Fi/LAN/Internet:** serie temporali complete, dashboard e confronto con il riferimento quando c'è connettività.
- **USB/SD/trasporto fisico:** esportazione dei log grezzi, foto del banco e valori di riferimento mediante supporti autorizzati.

## Software subito — esperimento da costruire
Generare **72 osservazioni artificiali** su due recipienti: superficie calma, increspata, eco assente, sensore inclinato, cambi di calibrazione, riavvio del logger, duplicati e consegne fuori ordine. Confrontare algoritmo ingenuo «ultimo valore ricevuto» e validatore che usa sequenze, timestamp qualificati, geometria e quality flag.

**Criteri PASS attesi:** nessun dato mancante convertito a livello zero; nessuna distanza fuori geometria pubblicata come volume certo; nessuna variazione attribuita alla fisica senza evidenza temporale; calibrazioni incompatibili non fuse automaticamente; i duplicati non alterano il grafico verificato. Misure da riportare: falsi cambi di stato, percentuale UNKNOWN, errore rispetto alla *verità sintetica* e latenza simulata di ricostruzione, senza chiamarli PDR radio reale.

## Prova hardware necessaria
Usare un piccolo recipiente di plastica stabile, sensore low-voltage protetto dagli schizzi, supporto rigido e una misura di riferimento indipendente (righello graduato o volume noto con geometria controllata). Variare **una condizione alla volta**: altezza reale, posizione del sensore, superficie calma/increspata e presenza di eco instabile. Registrare ogni lettura locale, i valori di riferimento e le ricevute applicative dei nodi. Non usare impianti reali, pompe o allarmi idrici. I limiti di precisione dipendono dall'esatto modello montato, da verificare sulla sua scheda tecnica.

## Privacy e sicurezza
Solo impianti e dati fittizi/scolastici autorizzati; vietate inferenze sui consumi domestici e coordinate di serbatoi privati. Elettronica separata dall'acqua, basse tensioni, supervisione del docente; nessun controllo remoto di attuatori. Autenticare il sensore e il profilo di calibrazione, perché un dato ritardato non deve diventare un falso stato attuale.

## Anti-duplicazione
**UC-191** riconcilia misuratori di portata per un bilancio; **UC-302** si occupa di contatori di impulsi dei pluviometri; **UC-144** riguarda risalite di bacini; **UC-171** qualità dell'acqua. Qui isoliamo il problema **eco di misura + geometria del recipiente + validità del livello** consegnato in ritardo.

## Riferimenti di contesto
- Siemens SITRANS LT500: esempi di criticità di misura di livello con turbolenza, schiuma e necessità di verifica: https://www.siemens.com/fi-fi/products/sitrans/lt500/
- Siemens SITRANS Probe LU240: requisiti di elaborazione dell'eco e installazione, non specifiche delle future schede scolastiche: https://www.siemens.com/en-gb/products/sitrans/probe-lu240/
