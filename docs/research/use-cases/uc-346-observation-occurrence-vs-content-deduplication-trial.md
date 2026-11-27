# UC-346 — Relay e IoT: contenuto identico, osservazioni distinte

**Stato 2026-11-27:** proposta, non implementata né collaudata. **Difficoltà:** media (identità degli eventi, persistenza, conflitti). Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Un sensore misura 20,0 °C a due istanti distinti; i byte del valore sono identici. Un relay trasporta inoltre la prima osservazione due volte. Deduplicare per hash del solo valore perde una misura reale; contare ogni ricezione gonfia invece il dataset. Bisogna distinguere contenuto, occorrenza applicativa e tentativo di consegna.

## Attori e scenario messinese
Due sensori o generatori fittizi, un gateway per sorgente, due relay volontari, cache/collector e docente. In laboratorio A produce dati, B e C li trasportano in finestre separate, D ricostruisce lo storico. In seguito checkpoint autorizzati a Milazzo, Venetico e Rometta possono replicare l'esperimento con studenti che trasportano le schede durante normali spostamenti; non si assume alcun collegamento intercomunale diretto.

## Perché PollicinoNet
Il riuso di byte già disponibili è utile proprio quando i contatti sono scarsi. Un manifest di occorrenza autentico lega `event_id` (sorgente pseudonima di campagna, generazione di boot persistente e contatore o UUID adeguato), hash completo del payload canonico, schema, finestra di osservazione e qualità temporale. Le copie di trasporto conservano lo stesso event_id; due osservazioni indipendenti hanno ID diversi anche se condividono il blob. Le correzioni sono nuove revisioni con riferimento esplicito all'evento; stesso ID e hash/metadata incompatibili = conflitto da isolare, non sovrascrittura. Non usare un semplice digest corto come identità né una firma come prova di verità della misura.
- DISCOVERY: hint di manifest/oggetto disponibile, non prova di presenza.
- EXACT: manifest verificato e blob esatto, anche recuperato da cache autorizzata.
- SEMANTIC: conteggio e riepilogo esplicitamente derivati, non sostituti delle osservazioni originali.

## Bearer
LoRa: alias di campagna, identificatori compatti verificabili e piccoli record entro budget reale dell'adapter; se il manifest non entra, solo discovery/richiesta. BLE: sincronizzazione locale di manifest; Wi-Fi/LAN/Internet: storico e blob mancanti; USB/SSD/trasporto fisico: cache offline autorizzate. Nessun bearer alternativo nascosto durante la prova LoRa-only.

## Test software proposto
Generare con seed fisso 24 eventi validi (inclusi 12 valori identici a coppie), 8 repliche di trasporto, 2 conflitti intenzionali di ID, consegne fuori ordine, reboot, hash errato, blob mancante e revoca. Confrontare (A) dedup per hash del valore, (B) conteggio per ricezione, (C) ledger per occorrenza + blob store content-addressed. Conservare la verità sintetica fuori dal sistema in prova.
**PASS:** i 24 eventi validi distinti sono ricostruibili quando completi; repliche non incrementano il conteggio; payload condivisi non sono rispediti inutilmente se cache autorizzata verificata; conflitti restano separati/in quarantena; evento con blob assente rimane incompleto; reboot non riusa ID già emessi. Contabilizzare byte di manifest, blob, ricevute e tentativi, non solo risparmio teorico dei blob. Se evidenza incompleta: INCONCLUSIVE. Nessun test eseguito.

## Hardware e misure necessarie
4–5 schede esistenti e due PC; iniziare con generatore sintetico o pulsante/LED innocuo, non serve sensore calibrato. Inviare ripetizioni controllate tramite relay diversi e contatti non sovrapposti; verificare persistenza al riavvio e confrontare log sorgente, relay e collector. Registrare denominatore dei tentativi, accettazioni, eventi distinti, byte, condizioni e configurazione effettiva. Nessuna PDR, copertura o airtime presunti.

## Privacy/sicurezza
Pseudonimi di campagna, non identificativi di studenti, nessun GPS o tracciamento; autenticazione del manifest, autorizzazione anche per cache, protezione degli hash di dati a bassa entropia (UC-278), TTL e limiti di storage. Non usare la deduplicazione come oracolo di presenza di contenuto privato.

## Distinzione dal catalogo e riferimenti
UC-130 deduplica chunk di artefatti, UC-175 evita doppi effetti di comandi, UC-249 codifica micro-fatti tipizzati, UC-230 verifica conformità tra bearer. Qui il criterio è conservare la molteplicità di osservazioni indipendenti riusando i byte identici. Complementare a UC-321 e UC-343.
Riferimento concettuale: [RFC 9171 §4.2.7](https://www.rfc-editor.org/rfc/rfc9171.html#section-4.2.7), identità di una richiesta di trasmissione distinta dal suo contenuto; non afferma che PollicinoNet implementi BPv7.
