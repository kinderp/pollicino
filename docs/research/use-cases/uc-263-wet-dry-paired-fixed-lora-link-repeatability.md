# UC-263 — Collegamenti LoRa dopo pioggia: ripetibilità delle prove a postazioni fisse

**Stato:** proposta documentale del 29 ottobre 2026; nessuna misura eseguita. **Difficoltà:** media per dataset e analisi, alta per controllo dei confondenti fisici. Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema risolto

Un collegamento fra due checkpoint scolastici funziona in una giornata asciutta: possiamo aspettarci risultati simili dopo la pioggia? Variazioni nel terreno/vegetazione bagnati, nell'installazione, nel rumore e nelle condizioni meteo potrebbero confondere il confronto. La distanza o una mappa previsionale da sole non bastano. **Non attribuire una differenza osservata alla pioggia senza un disegno sperimentale controllato.**

**User story:** come gruppo di studenti vogliamo ripetere lo stesso test radio fra *postazioni fisse autorizzate* in condizioni asciutte e dopo precipitazioni, registrando gli elementi che potrebbero alterare i risultati e quantificando ciò che rimane ignoto.

## Attori e perché PollicinoNet

Docente, due postazioni RX/TX, ricevitori indipendenti, 4–6 schede, optional pluviometro o stazione meteo, analisti e relay per consegna differita dei log. Lo store-and-forward porta in seguito gli **evidence pack** con configurazione, misure ed eventuali lacune a un collector disconnesso. Il protocollo di prova deve essere identico nelle sessioni e isolato per campagna (UC-256).

## Bearer

- **LoRa:** pacchetti di test compatti con ID e sequenza, senza cambiare la configurazione congelata; rigoroso budget di emissione.
- **BLE/USB:** estrazione locale dei registri e diagnostica non radio, secondo capability effettive della scheda.
- **Wi-Fi/Internet:** dataset, grafici, dati meteorologici di riferimento ed esecuzione dei confronti.
- **SD/USB/trasporto fisico:** dataset di osservazione per luoghi senza backhaul; relay volontari solo per trasporto dei riepiloghi, non per mappare gli spostamenti.

## Cosa testare subito in software

1. Generare un dataset **sintetico** con siti fissi, `trial_id`, coppia radio, configurazione/versione, condizioni dichiarate `DRY`/`POST_RAIN`/`UNKNOWN`, tempi di misura, altezza/assetto antenna, qualità del log e dati meteo con fonte.
2. Simulare sessioni abbinate con un effetto meteorologico ipotetico, cambiamenti indipendenti di interferenza/orario, alterazione dell'alimentazione e perdita di log; i dati simulati NON sono misure messinesi.
3. Calcolare ricezioni/trasmissioni solo quando il TX è **osservato** e RX è monitorato (UC-178/196/231). Non trasformare RX mancanti in RSSI = 0 né equiparare registro mancante a pacchetto perso.
4. Separare confronti entro la stessa coppia/postazione da differenze tra siti; controllare ora del giorno, altezza delle antenne, firmware, batteria, durata e numero di tentativi. Riportare intervalli e numerosità, non soltanto una media.
5. Rifiutare confronti con configurazione cambiata, classificazione pioggia senza fonte, tempi non compatibili, o denominatore di TX ignoto; conservare esplicitamente `UNCOMPARABLE`.

**PASS software:** nessun PDR inventato da dati incompleti; nessuna causalità dichiarata da sole correlazioni; prova ripetibile con stessi input e policy di esclusione.

## Prove fisiche e rete provinciale

Fase 1: due postazioni autorizzate all'interno della stessa scuola, senza esporre studenti alle intemperie, controllando l'antenna e la sicurezza elettrica. Fase 2: due coppie di checkpoint fra zone scolastiche di Messina, Villafranca, Rometta e Venetico. Raccogliere sessioni in periodi naturalmente asciutti e **dopo** la pioggia; non bagnare dispositivi o antenne a fini sperimentali. Stazioni meteo indipendenti se disponibili, ma nessun sensore aggiuntivo obbligatorio per avviare il protocollo.

Registrare TX effettivi, RX indipendenti, RSSI/SNR solo sulle ricezioni, frequenza/configurazione, direzione A→B e B→A (UC-232), condizioni meteo, temperatura dispositivo, variazioni della postazione e intervalli di incertezza. Dati soltanto di siti fissi, non di tragitti personali. Nessuna misura di PDR o portata è disponibile ora.

## Privacy, sicurezza, difficoltà e anti-duplicazione

Postazioni concordate con le scuole; ID temporanei, nessuna posizione personale, log minimizzati con retention limitata. Autenticazione delle capsule di misura e validazione manuale dei metadati. Trasmissioni conformi ai limiti di sottobanda e attrezzatura, nessuna trasmissione automatica intensiva durante maltempo e nessun sopralluogo su terreni instabili.

UC-259 confronta **previsioni del terreno vs postazioni holdout**; UC-211 studia l'effetto del montaggio antenna; UC-232 collega direzioni; UC-183 confronta politiche di routing; UC-197 trasporta osservazioni meteo. **UC-263 riguarda un confronto *ripetuto e appaiato* del medesimo collegamento al mutare delle condizioni dopo precipitazioni, con esplicita gestione dei confondenti.** Anche un risultato nullo documentato è informativo.
