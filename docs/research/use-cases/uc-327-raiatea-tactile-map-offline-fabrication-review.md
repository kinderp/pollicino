# UC-327 — Raiatea e mappe tattili didattiche: dal contenuto autorizzato al manufatto revisionato

**Stato:** proposta documentale del 20 novembre 2026. **Difficoltà:** medio-alta per il workflow, alta per accessibilità e valutazione dell'artefatto. Nessun prodotto stampato o validato dichiarato.

## Problema e destinatari
Un laboratorio scolastico desidera produrre una piccola mappa tattile di un **ambiente fittizio** per una lezione inclusiva. Un disegno digitale corretto dal punto di vista geometrico può risultare illeggibile al tatto se scala, distanze tra simboli, legenda e dettagli sono inadeguati; una stampante 3D non certifica l'accessibilità. Raiatea deve conservare fonte, licenza e revisioni; PollicinoNet rende disponibile il pacchetto fra laboratori scolastici non sempre collegati.

Attori: docente autore della mappa, docente/revisore di accessibilità, laboratorio di stampa 3D e controllo qualità, cache Raiatea, relay volontari e destinatari di una dimostrazione supervisionata. Nessuna raccolta di dati personali degli alunni.

## Perché PollicinoNet
Un avviso compatto di un nuovo pacchetto può arrivare presto; sorgenti, geometrie, file STL/SVG e istruzioni hanno dimensioni e controlli per cui richiedono un bearer ricco. Store-and-forward permette a un laboratorio di lavorare su revisioni autorizzate e restituire esiti di verifica anche giorni dopo. Il pacchetto non diventa RELEASED solo perché il file è stato consegnato o stampato.

## Bearer e oggetti
- **LoRa:** digest del manifest firmato, stato di disponibilità, richiesta breve, esito revisione.
- **BLE:** metadati o piccolo pacchetto di controllo vicino al laboratorio.
- **Wi-Fi/LAN/Internet:** sorgenti grafici, STL, istruzioni e prove fotografiche quando autorizzate.
- **SSD/USB/trasporto fisico:** oggetto digitale completo o manufatto fisico fra laboratori, con bearer registrato separatamente.

TactilePack = {pack_id, source_hash, edition, license, intended_learner_task, scale, tactile_symbol_legend, source_coordinate_system_or_synthetic, geometry_hash, printer_profile, approval_state, reviewer_role, revision_history}. La parola "mappa" non deve fare pensare a una carta di navigazione verificata.

## Prova software subito (proposta, non eseguita)
Creare tre piccole piante fittizie di aula con 10 simboli e 2 revisioni ciascuna. Un programma controlla: corrispondenza esatta sorgente/derivato, licenza presente, geometria non vuota/manifold dove applicabile, simboli troppo vicini rispetto a un parametro *configurabile da validare*, legenda assente, scala cambiata senza revisione, recupero offline di fonte e versione e presenza di approvazione umana.
- Un hash corretto non equivale a mappa accessibile.
- Geometria/legenda incompleta => REVIEW_REQUIRED, non READY.
- Revisioni arrivate fuori ordine non sostituiscono l'ultima versione approvata senza provenance.
- Differenziare consegna EXACT della mappa, stampa fisica e successiva **valutazione tattile**.

## Hardware dopo, poi eventuale rete messinese
Due PC scolastici, una stampante 3D supervisionata (se disponibile), campioni innocui senza spigoli, e 3–4 schede LoRa per i soli manifest/status. Testare localmente la possibilità di produrre un campione sicuro, verificarne dimensioni e caratteristiche; coinvolgere revisori esperti e, solo con consenso appropriato, persone che usano materiali tattili per una valutazione non invasiva. Tra Milazzo, Rometta e Venetico si possono spedire manifest e feedback in differita e far arrivare il pacchetto grande tramite Wi-Fi/SSD. **Non usare prototipi come dispositivi di orientamento o sicurezza reale**.

## Privacy e sicurezza
Niente mappe di abitazioni o tragitti di alunni, niente informazioni di accessibilità individuale associate a nomi. Solo contenuti fittizi o espressamente autorizzati, licenza verificata, niente stampa automatica di file eseguibili o comandi macchina non validati, file in sandbox; docente responsabile dell'approvazione e della sicurezza della stampante. Non confondere approvazione didattica, accessibilità universalmente garantita e validità per orientamento.

## Differenza dal catalogo e criterio PASS
UC-017 distribuisce tile di mappe, UC-047 lavori di fabbricazione, UC-192 materiali didattici accessibili, UC-208 osservazioni su percorsi accessibili, UC-316 guide culturali. Qui si collega **una derivazione cartografica tattile** a scala, leggibilità, verifica umana e accettazione del manufatto, mantenendo separata la consegna digitale dalla sua utilità.

Esito positivo software solo se manifest, controllo di geometria/versioni e stati di revisione superano test riproducibili; un risultato fisico richiede misure del campione e giudizio dei revisori, non è deducibile dal simulatore.

**Fonte:** Braille Authority of North America, Guidelines and Standards for Tactile Graphics, sez. 8.6, https://brailleauthority.org/tg/web-manual/tgmanual.html .
