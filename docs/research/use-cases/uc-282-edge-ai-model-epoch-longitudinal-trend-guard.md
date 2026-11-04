# UC-282 — Osservatorio edge AI: separare cambi di modello da cambi dell'ambiente

**Stato:** proposta documentale del **4 novembre 2026**, non implementata; nessun test né osservazione fisica. **Difficoltà:** medio-alta/alta. Il PHY LoRa congelato, MAC, driver e firmware **non cambiano**.

## Problema / user story

Due laboratori della provincia di Messina effettuano osservazioni ambientali tramite piccoli classificatori edge AI, per esempio **candidati eventi naturalistici** (solo dati sintetici all'inizio). Una scuola aggiorna il modello da V1 a V2 mentre l'altra resta su V1: i conteggi di `evento rilevato` cambiano. **Questo non prova che il fenomeno ambientale sia aumentato o diminuito**: potrebbe essere cambiata la sensibilità del classificatore o il metodo di campionamento.

**Come docente/scienziato scolastico** voglio che un rapporto o un'inferenza DNA non unisca automaticamente serie di modelli incompatibili. Occorrono epoche di modello, un riferimento comparativo comune e l'esito `NON_CONFRONTABILE` finché non esiste una validazione adeguata.

## Attori, nodi, applicazione e scenario Messina

Due checkpoint scolastici autorizzati (ad esempio Rometta e Venetico), due dispositivi edge/laptop, un revisore scientifico, servizio di raccolta Raiatea/DNA, 4–6 relay PollicinoNet eventualmente trasportati volontariamente **senza GPS né percorsi**. Eventuali altri siti a Messina/Villafranca in una fase successiva.

I relay store-and-forward possono consegnare prima gli eventi di V2 e soltanto dopo il manifest di V1 o le rettifiche; la ricostruzione deve usare il **tempo dell'osservazione**, la versione **effettivamente usata** e l'incertezza, non l'ordine di arrivo.

## PollicinoNet, livelli e bearer

- **DISCOVERY:** annuncia che un sito dispone di eventi, manifesto di modello o relazione fra epoche; non garantisce l'identità semantica dei conteggi.
- **EXACT:** hash del modello, pipeline/pre-processing, schema di output, versione di soglia, protocollo di campionamento e dataset di riferimento; verificare byte e identità.
- **SEMANTIC:** la classe `evento naturalistico candidato` è una *predizione*, non un'osservazione umana verificata.

**LoRa** trasporta eventi compatti/epoch ID/manifest hash autorizzati, se l'adapter li supporta. **BLE** sincronizza riepiloghi al contatto; **Wi-Fi/Internet/USB/SSD** trasportano manifest completi, fixture, piccoli modelli consentiti e report. **Trasporto fisico** permette di riportare dataset autorizzati per la valutazione. Non inviare modelli AI o flussi audio su LoRa, non eseguire modelli ricevuti senza il gate UC-279.

Schema applicativo di osservazione: `{site_code, observation_window, valid_sampling_duration, sensor_quality, model_exact_hash, preprocess_hash, threshold_epoch, predictions_count, uncertainty, source_evidence_ref}`. Evitare di pubblicare esatte coordinate dei siti sensibili o metadati che consentano tracciamento.

## Software immediato

1. Costruire 120 finestre **sintetiche** per sito, con ground truth noto. Simulare uno stesso fenomeno stabile e modelli `V1` e `V2` con sensibilità diversa; poi un secondo dataset in cui il fenomeno cambia davvero.
2. Introdurre aggiornamento scaglionato tra due siti, orologi incerti, campioni mancanti, ritardo dei manifest, ordine di consegna invertito e classificazioni errate.
3. In un piccolo dataset **di riferimento congelato e autorizzato**, eseguire *in simulazione* entrambi i classificatori o usare predizioni fixture. Calcolare differenze di predizione fra versioni e intervalli d'incertezza; la relazione è valida per quel riferimento, non una calibrazione universale.
4. Aggregatore ingenuo: concatena tutti i conteggi. Aggregatore corretto: raggruppa per `model_exact_hash + preprocess_hash + threshold_epoch + protocol_version`, segnala `MODEL_CHANGE`, `INSUFFICIENT_EVIDENCE` o `NOT_COMPARABLE`. Solo una politica di comparabilità esplicita, approvata, permette una serie unificata con disclaimer.
5. DNA/Raiatea non devono inferire `aumento delle specie` né `diminuzione ambientale` dai soli conteggi del classificatore. Salvare la provenienza del confronto e la versione della regola di aggregazione.
6. Fixture PASS/FAIL: nessun trend cross-version automatico; il modello aggiornato senza manifest rimane `UNKNOWN`; più tempo di campionamento non viene confuso con più eventi; una modifica ambientale reale sintetica può essere distinta *solo quando* i dati di riferimento lo consentono.

## Prove fisiche successive (nessuna eseguita)

In laboratorio, due PC/RPi con un dataset pubblico autorizzato o segnali interamente sintetici: prove su V1/V2 in condizioni identiche. Poi due stazioni scolastiche **fisse e autorizzate**; verificare qualità sensore, tempo e durata di campionamento; confrontare prima gli stessi modelli su input comuni; solo dopo introdurre rollout differito. 4–6 schede trasportano riepiloghi e stati di versione; Wi-Fi/USB i dati maggiori.

Nel caso bioacustico UC-273, **nessuna acquisizione di voci o audio ambientale negli spazi frequentati** senza valutazione e autorizzazioni specifiche. Il progetto può essere completato con dataset sintetici; non è necessario installare microfoni. Non attribuire agli animali cambiamenti rilevati da soli modelli. Misurare realmente ritardi di consegna, qualità del confronto e tassi di accettazione solo dopo implementazione e prove.

## Sicurezza, privacy, limiti

Autenticare manifest, vincolare eventi a hash delle versioni, applicare policy di autorizzazione e revoche, nessun download o deserializzazione automatica di modelli non fidati (UC-279). Niente profili di studenti o posizioni individuali, minimizzare eventi temporali, durata di conservazione limitata. Non basta una firma per dimostrare correttezza scientifica; anche il dataset di riferimento può non rappresentare tutti i luoghi. Distinguere `PREDICTED` da `HUMAN_REVIEWED`.

## Perché non è una variante già presente

- **UC-007 / UC-273:** producono e trasportano eventi edge AI; UC-282 previene **salti artificiali delle serie temporali** quando le epoche del modello divergono.
- **UC-038 / UC-210 / UC-140:** valutano modelli e feedback, ma non impongono una regola di **comparabilità longitudinale** dopo aggiornamenti asincroni.
- **UC-072 / UC-160:** monitoraggio drift e rollout/rollback; qui il problema è la **falsa conclusione ambientale** generata da conteggi di versioni differenti.
- **UC-127 / UC-272:** provenienza dell'inferenza e tempo di validità dei fatti; qui si richiede una verifica della **stabilità semantica della metrica** a cavallo del cambio modello.
- **UC-228:** bias nella selezione dei dati consegnati; UC-282 distingue bias di consegna da cambiamenti del classificatore.

**Risultato atteso:** un report che rifiuta esplicitamente i confronti ingiustificati, anche quando tutte le capsule sono state consegnate integre. Nessun test o risultato numerico reale è dichiarato.
