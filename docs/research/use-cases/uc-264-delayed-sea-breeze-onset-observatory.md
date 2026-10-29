# UC-264 — Osservatorio scolastico della brezza marina con eventi meteorologici differiti

**Stato:** proposta documentale del 29 ottobre 2026; nessuna stazione installata e nessun evento misurato. **Difficoltà:** media per software; alta per un'osservazione meteo credibile. Non è un servizio meteorologico operativo o un'allerta.

## Problema e storia concreta

Le scuole costiere della provincia di Messina vorrebbero confrontare **quando** si osservano cambiamenti compatibili con l'avvio della brezza marina. Se un dato raccolto a Spadafora arriva a Venetico tre ore dopo, il tempo di ricezione non è quello del fenomeno. Serie incomplete, orologi imprecisi e sensori poco affidabili possono falsare una ricostruzione.

**User story:** come docente di informatica e scienze voglio che più stazioni fisse raccolgano finestre di temperatura, vento (direzione e intensità) e, se disponibile, umidità, che un classificatore locale proponga una **possibile** transizione, e che PollicinoNet porti la segnalazione compatta e poi le serie originali alla classe per verifica.

## Attori, nodi e idoneità di PollicinoNet

Due o tre stazioni **fisse scolastiche** autorizzate, microcontrollore/sensori, 4–8 schede relay LoRa, PC del laboratorio, insegnante revisore, eventuale stazione meteorologica di riferimento. I relay studenti store-and-forward possono trasportare gli eventi e i dataset **senza condividere itinerari**. PollicinoNet trasporta prima eventi di dimensioni minime, poi prove complete su un bearer ricco; registra identificativo di schema, sensore, qualità del clock e provenienza.

## Bearer

- **LoRa:** evento compresso (`station_alias`, `window_id`, `candidate_onset_interval`, `time_uncertainty`, `quality_flag`, hash/ID dataset) entro il payload supportato; nessun flusso continuo ad alta frequenza.
- **BLE:** download locale di eventi e configurazioni, ove supportato.
- **Wi-Fi/Internet:** serie temporali complete, grafici, revisione umana e confronti con osservazioni di riferimento.
- **SD/USB/trasporto fisico:** export delle serie quando il link non basta.

## Esperimenti software senza hardware

1. Generare **serie artificiali** a passi temporali fissi con alcuni giorni con transizioni di direzione del vento e altri senza; includere vento sinottico, rumore, sensori con orientamento errato, clock drift, finestre mancanti e consegna ritardata.
2. Definire *prima* la regola di classificazione (una combinazione di andamento e orientamento locale, velocità, persistenza e contesto termico); evitare una singola soglia universale. Non fare inferenza della brezza dalle sole temperature.
3. Restituire `CANDIDATE`, `NOT_OBSERVED_WITH_VALID_WINDOW` o `UNKNOWN`, con un intervallo possibile di onset anziché un istante di falsa precisione. La revisione umana può rifiutare o correggere l'evento mantenendo la provenienza.
4. Mantenere distinti `observed_at` (con precisione e fuso/orologio dichiarati), `published_at` e `delivered_at`; riordinare per tempo di osservazione soltanto quando l'incertezza temporale lo consente (UC-123/93).
5. Confrontare su dataset sintetici con ground truth nota il numero di falsi positivi, mancati rilevamenti, copertura delle finestre e byte trasmessi; testare consegne duplicate e tardive, versioni di algoritmo non compatibili, manifest corrotto e revoche.
6. Quando disponibili dati reali, definire in anticipo un set holdout di giornate e una revisione indipendente per evitare di promuovere segnali dubbi a conclusioni certe.

**PASS software:** dati assenti diventano `UNKNOWN`, arrivi in ritardo non cambiano l'ora di acquisizione, nessun evento è presentato come certezza senza verifica, tutte le prove mantengono ID e qualità.

## Prova fisica e scenario Messina

Iniziare con due stazioni affiancate e confrontare letture/orientamenti; solo dopo collocare postazioni **autorizzate** in zone scolastiche costiere di Villafranca, Spadafora o Venetico, documentando ostacoli, altezza e calibrazione. Non assumere che una brezza 'avanzi' in ordine monotono fra località: orografia e venti di fondo possono renderne l'evoluzione non uniforme. Utilizzare sensori di vento **realmente disponibili e adeguati**, altrimenti il caso rimane simulato; la sola misura di temperatura non basta.

Misurare qualità dati e tempo, eventi proposti/verificati, TX/RX indipendenti, consegne e ritardi per bearer, buffer e consumo quando strumentato. Non pubblicare previsioni operative, consigli sanitari o avvisi alla popolazione.

## Privacy, sicurezza e novità rispetto al catalogo

Solo dati di postazioni pubbliche/consentite, niente audio/immagini di persone, movimenti studenteschi o identificativi personali. Firmare manifest e correzioni dei revisori, registrare versione del classificatore e calibrazione, limitare retention. Collocazione, alimentazione e gestione meteo devono essere approvate dagli istituti.

UC-003 è generico sensor courier; UC-037 misura transect mobili, UC-197 registra condizioni meteo legate al rischio incendi e UC-223 confronta ombra/sole. **UC-264 ricostruisce *eventi di transizione* con timestamp di osservazione, incertezza, ritardi di consegna e validazione umana; non si limita a una serie di temperature.**

Riferimento didattico/metodologico: Furberg et al. (2002), *The climatology of sea breezes on Sardinia*, DOI: [10.1002/joc.780](https://doi.org/10.1002/joc.780). È un riferimento sul metodo osservativo, non una misura della costa messinese.
