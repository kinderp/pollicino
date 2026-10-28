# UC-259 — Previsioni radio sui Peloritani contro misure reali, con checkpoint tenuti nascosti

**Stato:** proposta documentale del 28 ottobre 2026; nessun simulatore realizzato né misura fisica effettuata. **Difficoltà:** media per il software di confronto; alta per una campagna radio scientificamente controllata.

## Problema concreto e storia

Una carta teorica suggerisce che due postazioni scolastiche possano comunicare perché sono vicine. Fra le colline dei Peloritani, però, la distanza da sola non descrive ostacoli, profilo orografico, quota dell'antenna, edifici o interferenze. Come decidiamo dove posizionare i primi relay senza spacciare una previsione per una misura?

**User story:** come docente che prepara una rete didattica fra Messina, Villafranca, Rometta, Venetico e Spadafora voglio confrontare previsioni **registrate prima** delle prove con ricezioni realmente osservate in **checkpoint fissi autorizzati**, mantenendo alcune postazioni come insieme di test non usato per tarare il modello.

## Attori, nodi e ruolo di PollicinoNet

Docente responsabile, due postazioni radio fisse con antenne documentate, 4–8 schede disponibili, uno o due ricevitori/osservatori indipendenti, studenti analisti e, solo in una fase successiva, relay volontari store-and-forward. I relay mobili non vengono utilizzati per mappare i tragitti degli studenti; le misure di propagazione si svolgono inizialmente su siti fissi.

PollicinoNet può portare fra scuole manifest delle campagne, previsioni, ID dei test, prove di TX/RX e riepiloghi compatti anche quando i gateway non hanno Internet. Le mappe e i log completi viaggiano con un bearer più ricco. **Una predizione di potenza ricevuta non equivale a una predizione dimostrata di PDR né a una garanzia di collegamento.**

## Bearer e dati

- **LoRa:** pacchetti di prova identificati e limitati, con identico profilo radio già approvato; eventuali annunci compatti delle campagne. Non intervenire sul PHY LoRa congelato.
- **BLE:** estrazione locale dei log e diagnostica ove l'hardware lo permetta.
- **Wi-Fi/LAN/Internet:** modelli, profili altimetrici, mappe, registri TX/RX e analisi.
- **USB/SD/trasporto fisico:** log grezzi e raccolte di misure quando manca connettività.

## Contratto scientifico e software testabile subito

1. Definire un dataset di checkpoint **fissi**, quota/altezza antenna, configurazione TX/RX invariata, ID esperimento, istanti delle finestre di misura e unità dei dati. Non pubblicare posizioni personali.
2. Registrare due baseline **prima** di conoscere le misure: (A) semplice distanza/visibilità geometrica, (B) modello che utilizza il profilo del terreno. ITU-R P.1812-8 è un possibile riferimento metodologico (https://www.itu.int/rec/R-REC-P.1812/en), non una certificazione di accuratezza locale e non va invocato senza dati e ipotesi sufficienti.
3. Separare siti di calibrazione e siti **holdout**; vietare di ritoccare predizioni holdout dopo aver letto i log. Congelare commit, versione del terreno, parametri, seed e unità.
4. Simulare ora un piccolo territorio artificiale con ostacoli, modelli imperfetti, ricevitori intermittenti e log mancanti. Testare lo schema, i calcoli, gli intervalli di incertezza e le regole di esclusione senza fingere di avere misure della provincia.
5. Per un invio, distinguere TX richiesto, TX realmente effettuato, RX osservato e RX non osservabile. Calcolare PDR soltanto su un denominatore di TX verificato e con riceventi monitorati (UC-178/231); raccogliere RSSI/SNR solo sulle ricezioni reali, senza imputare un valore numerico ai pacchetti mancati.
6. Confrontare errore delle previsioni del livello radio, variabilità tra sessioni, copertura degli intervalli di incertezza e, separatamente, probabilità empirica di ricezione. Evitare conclusioni oltre le posizioni realmente campionate.

**Criterio PASS software:** lo strumento rifiuta dati senza configurazione/epoca, preserva le predizioni pre-registrate, non confonde no-RX con log assente, distingue calibration/holdout e produce riepiloghi riproducibili. Non si dichiara in anticipo quale modello vincerà.

## Prova fisica necessaria

Avviare con due siti dello stesso complesso scolastico o due checkpoint autorizzati, RX indipendente e 4 schede; solo dopo passare a più siti della provincia, con 4–8 schede. Annotare antenne, orientamento, alimentazione, condizioni e altezza di montaggio, data e durata; ripetere sessioni per stimare variazione temporale. Nessuno studente deve percorrere strade per inseguire il segnale. Scegliere frequenza/potenza/duty cycle nel regime applicabile alle schede e al sito: riferimento generale ETSI EN 300 220-2 (https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.03.01_60/en_30022002v030301p.pdf), ma verificare le sottobande e le condizioni normative italiane effettivamente applicabili. **Nessun risultato di copertura, PDR o autonomia è disponibile da questo lavoro.**

## Privacy, sicurezza e differenza rispetto ai casi esistenti

Usare ID temporanei, sedi pubbliche/autorizzate o coordinate di soli punti fissi quando necessario; non registrare traiettorie degli studenti, dispositivi personali, nomi o orari individuali. Log firmati o hashati, conservazione limitata, consenso della scuola, separazione della campagna UC-256. Evitare trasmissioni su infrastrutture non autorizzate.

**Non duplicato:** UC-103 seleziona posizioni dei relay, UC-183 confronta routing, UC-196 studia diversità di ricezione, UC-211 le antenne e UC-232 l'asimmetria A↔B. Qui si verifica **la capacità predittiva e l'incertezza di un modello del terreno su siti holdout**, prima di usarlo per decidere il deployment. Nessuna modifica a PHY/MAC/driver/firmware.
