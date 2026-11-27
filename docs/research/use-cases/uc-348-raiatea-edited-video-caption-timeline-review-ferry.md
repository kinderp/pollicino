# UC-348 — Raiatea: sottotitoli accessibili dopo il montaggio di una lezione

**Stato 2026-11-27:** proposta, nessun test o video reale esaminato. **Difficoltà:** medio-alta (lineage temporale, editing e revisione). Nessuna modifica al PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Due scuole condividono una lezione video con sottotitoli. Una revisione taglia i primi dieci secondi o sposta una spiegazione; il vecchio file WebVTT è ancora integro ma ora può descrivere l'azione sbagliata al momento sbagliato. Non basta verificare l'hash del sottotitolo o conoscere la trascrizione.

## Attori e scenario
Docente autore, laboratorio video/Raiatea, eventuale modello ASR locale, revisore, cache di sedi e relay volontari. Milazzo produce un video dimostrativo con animazioni e voce sintetica; un laboratorio a Venetico prepara sottotitoli; a Rometta una cache riceve prima l'avviso di revisione, poi i file. Nessun video di alunni o collaborazione presupposta.

## Perché PollicinoNet
La timeline di montaggio può essere piccola rispetto al video: distribuire versione, richieste di revisione e stato in differita; riusare solo segmenti verificati senza ripetere tutti i contenuti. Manifest con hash del video esatto e base temporale, hash WebVTT, lingua, versione, cue ID e intervallo, segmento audio/video di origine, edit decision list (intervalli originali→nuovi), note su audio significativo, esito e revisore. Mappe temporali solo per modifiche note: un taglio/spostamento non equivale automaticamente a nuova approvazione. Cue attraversato da un taglio, audio sostituito, velocità cambiata senza mapping verificato, timeline ambigua o revisione assente = da revisionare; non indovinare.
- DISCOVERY: versione media e disponibilità derivato, senza testo privato.
- EXACT: file, manifest e mappa temporale verificati, non semplice hint.
- SEMANTIC: bozza ASR e stato di accessibilità; non equivalgono a sottotitoli approvati.

## Bearer
LoRa: hint/annunci di invalidazione e richieste compatibili col budget; BLE: piccoli metadati o cue autorizzati; Wi-Fi/Internet: WebVTT, sorgenti, video e prove; USB/SSD trasporto fisico per media grandi. Il video non si trasmette su LoRa.

## Software proposto
Creare video fittizio di 60 secondi con marker visivi/audio, 12 cue e quattro revisioni (taglio iniziale, rimozione in mezzo, riordino, sostituzione audio). Testare consegna WebVTT vecchio dopo nuovo manifest, cue sovrapposti legittimi, cue fuori durata, cue che attraversa un taglio, hash non corrispondente e revisione tardiva. Confrontare riuso cieco, invalidazione totale e riuso selettivo con mapping e revisione. PASS: nessun file obsoleto viene associato come approvato a video nuovo; intervalli dei segmenti conservati sono trasformati correttamente nei casi deterministici; cue ambigui bloccati; approvazione vincolata esattamente a media, track e lingua. Metrica: cue da rivedere, falsi riusi, byte e tempo di revisione, senza presumere accuratezza ASR. Se il nodo non conosce una nuova versione, mostra solo quella localmente nota e non dichiara freschezza globale. Test non eseguito.

## Hardware e verifica umana
Due PC/browser con player locale e 3–4 schede; video sintetico, track WebVTT, rete di test. Disconnettere cache e inoltrare avvisi di nuova versione attraverso due incontri. Poi riprodurre video e sottotitoli per controllare sincronizzazione, testo, identificazione parlanti e suoni rilevanti. Verifiche di accessibilità con revisori competenti; validità sintattica non prova accessibilità. Nessuna misura radio o risultato assistivo dichiarato.

## Privacy/sicurezza
Solo materiali propri o con licenza appropriata, voce sintetica o adulta autorizzata, nessuna ripresa di minori o dati scolastici riservati. Evitare invio cloud senza autorizzazione; accesso per policy, revoca e protezione metadati. Non riassociare didascalie tra video diversi in base alla sola similarità.

## Distinzione e fonti
UC-192 tratta pacchetti accessibili, UC-120 invalidazione di derivati, UC-312 trascrizioni con consenso, UC-342 significato matematico. Qui si verifica la corrispondenza temporale di cue a segmenti dopo editing, con possibile riuso selettivo sottoposto a revisione.
Riferimenti: [W3C WebVTT](https://w3c.github.io/webvtt/) (cue temporizzati); [W3C WAI H95](https://www.w3.org/WAI/WCAG22/Techniques/html/H95) (track di sottotitoli con informazioni audio rilevanti). Non si dichiara conformità WCAG automatica.
