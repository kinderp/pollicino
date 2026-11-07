# UC-290 — Osservatorio didattico della luminosità del cielo notturno tra costa e Peloritani

**Stato:** proposta documentale del **7 novembre 2026**, non implementata. Nessuna osservazione, test software o misura fisica eseguiti. **Difficoltà: medio-alta/alta**, per comparabilità delle misure. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e scenario

Scuole tra Villafranca, Rometta, Venetico e l'entroterra peloritano vorrebbero studiare come cambia la luminosità del cielo notturno in siti **fissi e autorizzati**. Senza protocollo, un valore raccolto con cielo nuvoloso, Luna presente, strumento diverso o orario non confrontabile può sembrare un trend di inquinamento luminoso che non è dimostrato. Anche la mancata misura non deve diventare una notte «buia».

**Attori:** docenti di Scienze/Telecomunicazioni/Informatica, due o tre stazioni fisse scolastiche, custodi autorizzati, un revisore di dataset, 4–8 relay LoRa; volontari degli studenti solo per trasferimenti di capsule in orario ordinario. **Nessun sopralluogo notturno richiesto agli studenti.** La misura avviene in modo automatico o con supervisione adulta autorizzata.

## Perché PollicinoNet e bearer

Le stazioni possono essere offline per giorni. Una capsula piccola comunica `OBSERVATION_AVAILABLE` o `NOT_VALID` e riferimenti alla misura; i dettagli e le serie sono recuperati più tardi. Le cache diffondono correzioni e metodi senza pretendere connessioni continue.

- **LoRa:** digest e stato qualitativo, finestra di osservazione e ID opaco se l'adapter supporta dimensioni adeguate.
- **BLE:** interrogazione locale della stazione, se disponibile.
- **Wi-Fi/Internet:** serie complete, metadati e report revisionati.
- **USB/SD/trasporto fisico:** dataset e calibrazioni tra scuole in assenza di connettività.
- **DISCOVERY:** disponibilità di finestra; **EXACT:** misura e manifest versionati verificati; **SEMANTIC:** confronto o interpretazione *solo* dopo qualità e revisione.

## Contratto dati e interpretazione

`SkyWindow={station_public_code, window_id, instrument_class, calibration_id?, protocol_version, window_start/end, clock_uncertainty, moon_condition, cloud_condition, obstruction_condition, valid_samples, planned_samples, sky_metric_name, unit, value?, method_id, review_status, evidence_hash, revision_of?, source}`.

Distinguere `NOT_SAMPLED`, `SAMPLED_INVALID`, `PARTIAL`, `VALID_PENDING_REVIEW`, `VALID_REVIEWED`. `NOT_SAMPLED` non significa assenza di luce. Un comune luxmetro didattico **non equivale automaticamente** a un misuratore di luminanza del cielo calibrato: vietato mischiare unità o metodi senza validazione. Non ricavare causalità «un comune illumina più di un altro» da dati non appaiati; la copertura nuvolosa può aumentare o diminuire la luminanza osservata a seconda delle condizioni.

## Software immediato — non eseguito

1. Generare 30 finestre per ciascuna di 3 stazioni sintetiche: alcune con Luna, nubi, orologi imprecisi, sensori di classe diversa, misura assente e correzioni tardive; fissare seed e *ground truth* della qualità.
2. Simulare tre cache e sei relay intermittenti: ricezioni fuori ordine, revoche, duplicati e serie caricate prima o dopo i digest LoRa.
3. L'aggregatore deve includere nel confronto **solo finestre compatibili** per metodo, unità, calibrazione e condizioni dichiarate; le altre sono `NOT_COMPARABLE`, mai zeri.
4. Calcolare numero di finestre valide e copertura temporale; ogni output iniziale mostra `source=SIMULATED`. Le eventuali variazioni non ricevono automaticamente l'etichetta «inquinamento causato da X».
5. Esportare test `PASS/FAIL/UNKNOWN/NOT_TESTED` e un manifest firmabile delle revisioni.

**Accettazione:** nessuna notte saltata è zero; due unità differenti non entrano nella stessa media; una revisione ritardata non duplica la finestra; assenza di metadati Lunari/nubi non produce un trend certo; tutte le versioni esatte sono distinguibili.

## Prove hardware necessarie

Prima **in aula**: due PC, 4–6 schede, 2 stazioni artificiali che generano valori fittizi, consegna di digest e recupero esatto di report. Poi, con autorizzazioni, **due/tre postazioni fisse** con sensori appropriati per la luminosità del cielo e metodi documentati, orologi controllati e misure di condizioni meteorologiche; verifiche incrociate e calibrazione di riferimento quando necessarie. Conservare dati grezzi pertinenti e annotare quale strumento ha prodotto ogni osservazione. Relay degli studenti soltanto per trasporto differito, non misurazioni notturne mobili.

Nessuna copertura LoRa, autonomia, PDR o qualità ambientale dichiarata senza misure reali. Evitare installazioni su tetti/quote pericolose e puntamenti verso finestre abitate; rispettare sicurezza elettrica e normativa radio effettiva.

## Privacy e distinzione dal catalogo

Esclusivamente **codici pubblici di siti istituzionali autorizzati**, senza abitazioni private, volti, registrazioni audio/video, identità, posizioni di studenti o orari individuali. Conservazione limitata e revisione del docente. Non è monitoraggio di persone o certificazione scientifica.

**UC-264** studia brezza marina, **UC-242** rumore ambientale, **UC-223** differenze termiche ombra/sole, **UC-187** ripetizione protocolli scientifici, **UC-282** comparabilità edge AI. **UC-290** introduce un dataset scientifico *specifico* di **luminosità del cielo notturno** con strumento, unità, condizioni lunari/nuvolose, validità e comparabilità di finestre distribuite.

Fonte metodologica: [Kyba et al. (2013), *Citizen Science Provides Valuable Data for Monitoring Global Night Sky Luminance*, Scientific Reports](https://doi.org/10.1038/srep01835). Riferimento allo studio citizen science, **non** equivalenza automatica fra sensori o prova relativa ai Peloritani.
