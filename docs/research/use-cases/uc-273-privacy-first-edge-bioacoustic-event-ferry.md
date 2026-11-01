# UC-273 — Biodiversità didattica: eventi bioacustici edge AI senza distribuire audio

**Stato:** proposta documentale del **1 novembre 2026**. Nessun sensore installato, classificatore validato o dato di campo misurato. **Difficoltà:** alta (privacy acustica, qualità scientifica, ML e disponibilità energetica). PHY LoRa congelato invariato.

## Problema e scenario nella provincia di Messina

Scuole fra Villafranca, Rometta, Venetico e le aree autorizzate ai piedi dei Peloritani potrebbero confrontare **eventi candidati** compatibili con richiami di uccelli o altri segnali naturalistici, senza Internet continuo. Trasmettere audio non è appropriato alla capacità LoRa e può violare la privacy; inoltre un classificatore può sbagliare facilmente con vento, traffico e altri suoni.

**User story:** come gruppo scolastico di Scienze e Informatica voglio raccogliere **solo conteggi e indicatori aggregati di eventi biologici candidati**, con durata di osservazione, modello e incertezza, in modo che un'altra scuola possa verificarli successivamente senza accedere a registrazioni di persone. Non si pretende di stimare popolazioni o riconoscere con certezza specie.

## Attori, nodi e ruolo della rete

Due stazioni **fisse, autorizzate e segnalate**, un microfono che elabora **in memoria volatile** su dispositivo locale (computer/edge board), un docente revisore e 4–8 schede PollicinoNet con alcuni relay volontari store-and-forward. Nella fase iniziale si usano **soltanto file sintetici o registrazioni naturalistiche liberamente utilizzabili e senza voci**, non ascolto ambientale. La rete porta report piccoli a una cache scolastica, anche quando le stazioni sono offline. Un eventuale dispositivo LoRa **non è tenuto a eseguire il modello AI**: può limitarsi a inoltrare le capsule prodotte dal nodo edge.

## Contratto delle osservazioni

Report firmato/versionato con `station_pseudonym`, `coarse_site_class`, `window_start`, `window_duration`, `valid_observation_seconds`, `model_id/hash`, `taxonomy_version`, `candidate_event_type`, `candidate_count`, `confidence_bucket`, `quality_flags` (vento/rumore/sensore non disponibile), `review_status`, `exact_report_hash`. Non includere dati audio, trascrizioni vocali, coordinate puntuali di nidi o identità di osservatori.

Separare stati `CANDIDATE`, `REVIEWED`, `REJECTED`, `UNKNOWN`. **Zero eventi osservati** significa zero **solo** in una finestra valida; un microfono spento, non verificato o con forte rumore equivale a `MISSING/UNCERTAIN`. La frequenza dei candidati va contestualizzata alla durata di osservazione; non scambiare la somma dei pacchetti ricevuti per numero di animali o specie. Gestire deduplicazione e revisioni ritardate.

## Bearer

- **LoRa:** hash/riferimento ed evento molto compatto o riepilogo per finestra, **solo se payload e budget consentono**; vietato audio o streaming.
- **BLE:** configurazione e recupero locale autorizzato di report.
- **Wi-Fi / Internet:** trasferimento di modelli/dataset con licenze verificate, statistiche e revisione dei report.
- **USB/SD / trasporto fisico:** pacchetti modello e report completi fra laboratori senza rete; l'audio di campo **non** viene trasportato.
- `DISCOVERY` segnala un nuovo report, `EXACT` verifica il report e il modello; `SEMANTIC` è soltanto una **classificazione probabilistica**, non una verità scientifica.

## Primo esperimento senza hardware

Generare 60 finestre sintetiche di 10 minuti con verità artificiale nota: eventi veri, falsi positivi, falsi negativi, rilevazioni duplicate, periodi di vento, nessun campione, orologi imprecisi, pacchetti fuori ordine e una revisione tardiva. Per la fase ML, usare **soltanto** un piccolo dataset pubblico con licenza compatibile e senza persone, ma il test di rete non ha bisogno di un LLM o di un modello reale.

**Criteri PASS software:** nessuna finestra non valida trasformata in zero; deduplicazione delle revisioni; conteggi candidati indipendenti dall'ordine di arrivo; firma/hash verificati; reporting di precision/recall **solo sul truth set artificiale o su etichette verificate**, mai presentato come accuratezza nel Messinese; nessun audio nel payload o nei log. Confrontare baseline manuale/sintetica, evento compatto e trasferimento dati integrali solo sul banco, riportando byte e costi del modello.

## Esperimento fisico e limiti

Solo dopo autorizzazione scolastica e valutazione privacy: due siti fissi controllati e lontani da conversazioni, due dispositivi edge/microfoni adeguati, 4–8 schede LoRa, due ricevitori indipendenti e PC. Configurare l'elaborazione **senza salvataggio o trasmissione di audio grezzo**; interrompere l'osservazione se il contesto non permette di evitare la cattura di conversazioni. Valutare un piccolo campione con osservazione naturalistica manuale supervisionata, senza registrare persone. Documentare durata utile, qualità, modello/versione, alimentazione, contatti e ricevute applicative; misurare RX/TX/ritardi/energia soltanto con strumenti appropriati.

Nessun sistema di sorveglianza, riconoscimento vocale, riconoscimento di persone o localizzazione degli studenti. Non pubblicare ubicazioni dettagliate di specie sensibili, né dichiarare risultati ecologici definitivi. Dati privati o non autorizzati restano fuori dagli esperimenti.

## Privacy e sicurezza

Autorizzazioni e informativa, revisione preventiva dell'impatto del sensore acustico e delle licenze del modello. Report aggregati e pseudonimi per stazioni, non persone; cifratura quando necessario, firme di manifest, accessi limitati, scadenza e cancellazione verificabile dei buffer. Valutare il rischio che anche classificazioni rare rivelino posizioni sensibili; preferire aree grossolane e pubblicazione ritardata. Usare relay degli studenti solo su base volontaria e senza ricostruire percorsi.

## Anti-duplicazione

- **UC-007** è l'architettura generale di un `Edge AI Event Scout`; UC-273 è un **protocollo scientifico bioacustico privacy-first** con sforzo di osservazione, tassonomia, revisioni, validazione sul campo e divieto esplicito di audio.
- **UC-242** misura indicatori di rumore senza attribuire significati biologici; **UC-234** conta visite di impollinatori, preferendo nessun microfono. Questa nuova proposta riguarda l'errore di classificazione di eventi naturali acustici e l'eventuale necessità di non catturare audio.
- **UC-101/140** possono essere riutilizzati per disaccordi fra modelli ed etichette differite. Non duplicare il motore di verifica generale.

**Output atteso:** una campagna educativa e un catalogo di eventi **candidati**, non una mappa scientifica della biodiversità o dati fisici già raccolti.
