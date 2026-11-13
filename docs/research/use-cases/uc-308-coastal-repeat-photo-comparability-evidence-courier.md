# UC-308 — Foto ripetute della costa messinese: evidenze confrontabili, non false misure di erosione

**Stato al 13 novembre 2026:** proposta documentale; nessun test o sopralluogo eseguito. **Difficoltà:** medio-alta per la raccolta; alta per eventuali misure quantitative. PHY LoRa congelato e stack radio invariati.

## Problema concreto
Due fotografie della stessa spiaggia, scattate con angoli, zoom, livello del mare o condizioni del moto ondoso diversi, possono far apparire un arretramento della battigia che non dimostra una perdita stabile di spiaggia. Inoltre le foto possono contenere volti o targhe che non devono passare a relay volontari senza adeguata autorizzazione.

**Domanda:** possiamo costruire un archivio didattico distribuito di foto da punti fissi con metadati di confrontabilità e segnare le osservazioni non utilizzabili, senza presentarle come misure ufficiali di erosione?

## Attori, nodi e scenario provincia di Messina
Docenti di scienze e informatica, postazioni fotografiche autorizzate e statiche, due o tre cache scolastiche, revisori umani, schede relay e un eventuale processo di allineamento immagini su PC. Scenario **ipotetico**: tratti costieri accessibili e autorizzati nell'area Rometta–Spadafora–Venetico. Nessun punto di installazione, percorso, copertura radio o permesso viene presunto.

## Perché PollicinoNet
Una fotografia è troppo grande per essere spostata su un canale a bassa capacità. PollicinoNet può invece annunciare un'osservazione compatta, consegnare una richiesta di revisione in ritardo, e trasferire il documento EXACT quando due cache possono scambiarsi dati su bearer ricchi o attraverso un supporto scolastico. È un uso distinto da un semplice “album fotografico”: serve a riconciliare **qualità del rilievo, versione del protocollo e revisioni**.

- **DISCOVERY:** ID di postazione pubblica, data grossolana, presenza di un rilievo, schema/versione, senza identificativi dell'autore.
- **EXACT:** hash dell'immagine approvata e dei metadati autorizzati, coordinate della postazione solo se pubblicabili, versione della maschera privacy/review.
- **SEMANTIC:** etichetta visiva descrittiva e ipotesi da verificare, **mai diagnosi automatica di erosione**.

## Bearer
- **LoRa:** annuncio di nuovo rilievo, richiesta e esito di revisione in forma molto compatta, solo se tecnicamente supportato.
- **BLE:** scambio di schede descrittive fra postazione e dispositivo scolastico.
- **Wi-Fi/LAN/Internet:** foto, immagini registrate, analisi, confronti e report.
- **USB/SSD/trasporto fisico:** album di prova cifrato/autorizzato fra scuole.

## Modello minimo di dato
**PhotoObservation**: ID postazione, ID osservazione sintetico, data/ora e sua incertezza, tipo obiettivo/focale o zoom quando noto, prova della stabilità dell'inquadratura, note su onde/marea e meteo se documentate, hash dell'originale ad accesso limitato, hash del derivato condivisibile, esito di revisione privacy, revisione scientifica, protocollo. Stati: **COMPARABLE_QUALITATIVE**, **NEEDS_REVIEW**, **NOT_COMPARABLE**, **MISSING_CONTEXT**, **PRIVACY_BLOCKED**.

## Esperimento software immediato — non eseguito
Generare **18 immagini sintetiche** di una linea di battigia artificiale in tre fasi, con geometrie volutamente variate: stessa costa e zoom differente, camera spostata, livello acqua fittizio, occultamento, sfondo con silhouette inventate, metadati assenti. Simulare tre cache e consegne fuori ordine. Fare controllare da una regola conservativa i prerequisiti di confronto, mantenendo distinta una **timeline qualitativa** da una misura quantitativa calibrata.

**Criteri di accettazione futuri:**
1. Una foto non revisionata o contenente identificatori riconoscibili non diventa oggetto condivisibile.
2. Differenze di zoom/inquadratura non documentate diventano **NOT_COMPARABLE**, non “erosione osservata”.
3. Un rilievo mancante non è un rilievo negativo e una foto consegnata tardi conserva la data di acquisizione.
4. Le versioni originali e le revisioni hanno hash distinti; gli oggetti non autorizzati non sono annunciati pubblicamente.
5. Nessun esito di modello AI è promosso a misura fisica senza validazione indipendente e revisione esperta.

## Prove reali necessarie
Prima **due PC e quattro schede LoRa** per annuncio/recupero in laboratorio, con foto interamente sintetiche. In una seconda fase, una postazione di osservazione già autorizzata su suolo sicuro, senza accesso ad argini pericolosi o zone interdette, con supporto fotografico fisso se permesso. Misurare trasferimenti, ricevute app, tempi osservazione→revisione, esiti di confrontabilità. Per stimare il movimento reale della linea di costa servono **controlli fotogrammetrici, riferimento di livello del mare, geometria ed esperti**; non si deduce da sole foto casuali.

## Privacy, sicurezza e confini
Non richiedere dispositivi personali o GPS continuo a studenti. Evitare riprese di persone/targhe; se accidentalmente presenti, non distribuire la foto finché la revisione e le misure di minimizzazione non risultano valide. Non divulgare postazioni in aree protette o pericolose; rispettare licenze e autorizzazioni. Niente segnalazioni ufficiali di rischio o avvisi di sicurezza costiera.

## Non duplicazione
**UC-060** distribuisce immagini come evidenze in generale, **UC-116** verifica osservazioni di citizen science, **UC-285** conta rifiuti spiaggiati, **UC-296** ancora citazioni ai PDF. **UC-308** valuta specificamente **ripetibilità del punto fotografico e confondenti della linea di costa** prima di confrontare immagini distribuite.

## Riferimento scientifico
Harley & Kinsela, *CoastSnap: A global citizen science program to monitor changing coastlines*, Continental Shelf Research (2022), https://doi.org/10.1016/j.csr.2022.104796 . CoastSnap usa una postazione con inquadratura controllata; le misure quantitative richiedono geometria, allineamento e trattamento delle condizioni idrodinamiche. Non implica che PollicinoNet abbia già eseguito prove equivalenti.
