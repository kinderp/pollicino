# UC-296 — Raiatea: citazioni verificabili anche quando cambia il PDF originale

**Stato:** proposta documentale del **9 novembre 2026**; non implementata/testata. **Difficoltà:** medio-alta/alta (ancore robuste, OCR, versioni concorrenti, revisione umana). Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto e scenario messinese

Due classi di Informatica, a Rometta e Venetico, collaborano alla base di conoscenza di una lezione su DNS/HTTP. Una versione di un PDF o delle dispense contiene una fonte per il claim `C-07` alla pagina 24. Una nuova edizione inserisce una pagina all'inizio e corregge una frase; un secondo laboratorio ha soltanto la versione precedente e ha prodotto un riferimento da testo OCR. **Il numero di pagina da solo non prova che l'affermazione sia davvero sostenuta dalla fonte aggiornata.** Un LLM non deve dichiarare `VERIFICATO` solo perché ha riconosciuto un titolo simile.

**Story:** «Voglio che la citazione a una fonte rimanga verificabile rispetto all'esatto documento usato, e che ogni modifica di pagina/edizione richieda una riconvalida dichiarata».

## Attori e perché PollicinoNet

Docente revisore, autori dei claim, Raiatea, 2–3 cache scolastiche, relay degli studenti, eventuale servizio OCR isolato e lettore locale di PDF. Il documento potrebbe essere disponibile solo in una sede e la revisione arrivare in differita. PollicinoNet trasporta un **avviso breve** che una fonte/claim richiede revisione, poi recupera la versione esatta dell'oggetto attraverso un bearer più capiente. La provenienza delle asserzioni resta separata dall'ordinamento dei messaggi.

- **DISCOVERY:** ID opachi della fonte, versione del catalogo, stato compatto dei claim da revisionare.
- **EXACT:** hash del PDF originale, pagina in coordinate del file, eventuale ancoraggio a bounding box/segmento di testo e hash del claim, versione OCR e identità del revisore.
- **SEMANTIC:** possibili passaggi corrispondenti suggeriti per facilitare il controllo; **mai promuovere automaticamente un suggerimento a conferma della fonte**.

## Bearer

**LoRa** solo avvisi compatti di revisione/versione e riferimenti opachi autorizzati; **BLE** per sincronizzare lo stato breve vicino ai checkpoint; **Wi-Fi/LAN/Internet** per PDF, figure, indici e copie confrontate; **USB/SSD o trasporto fisico** per distribuzione autorizzata di documenti completi. Non trasferire PDF su LoRa.

## Dati e stati proposti

`SourceVersion = {source_id, exact_sha256, edition?, page_count?, license_scope, observed_at, ocr_tool_version?}`.

`ClaimAnchor = {claim_id, source_exact_sha256, quote_or_excerpt_hash?, pdf_page_index?, printed_page_label?, section_id?, region_bbox?, anchor_method: TEXT|IMAGE|MANUAL, evidence_ref?, reviewer_role?, decision_epoch}`.

`AuditState = VERIFIED_EXACT_SOURCE | REVIEW_REQUIRED | MISSING_SOURCE | CONFLICTING_CANDIDATES | NOT_AUTHORIZED | NOT_TESTED`.

Una citazione su una versione A non è automaticamente valida su B; una pagina numerata diversamente non viene riscritta in modo silenzioso. La corrispondenza del testo OCR con il testo PDF può essere ambigua (figure, colonne, formule) e richiedere confronto della pagina renderizzata e giudizio umano. La possibilità di leggere il documento deve rispettare diritti e autorizzazioni.

## Esperimento subito, soltanto software

1. Generare **due piccoli PDF sintetici** e un catalogo fittizio di 12 claim: versione A e B con pagina inserita, righe spostate, frase corretta, figure e due paragrafi simili. Le versioni sono controllate da hash.
2. Distribuire artificialmente gli indici fra tre cache offline; ritardare la pubblicazione della versione B e mescolare le decisioni dei revisori.
3. Verificare che claim A restino `VERIFIED_EXACT_SOURCE` **solo per A** e passino a `REVIEW_REQUIRED` per B finché la fonte B non viene esaminata.
4. Introdurre OCR errato, estratti inventati, pagina mancante, fonte non autorizzata, due edizioni con titoli identici e un replay di una precedente approvazione; il sistema non deve inventare pagina né citazione.
5. Confrontare un approccio «pagina e titolo» contro ancoraggio con hash/versione e approvazione. Tracciare mismatch, falsi `VERIFIED`, stato di revisione, dimensione delle capsule e necessità di richiedere la fonte completa.

**Accettazione:** zero false conferme per i casi artificiali noti; quando l'oggetto manca, stato `MISSING_SOURCE`; quando è protetto, `NOT_AUTHORIZED`; ogni conferma punta alla **versione esatta** effettivamente consultata. Nessun test eseguito: PASS/FAIL da calcolare soltanto dopo un prototipo.

## Prova fisica e privacy

Due PC inizialmente scollegati, 4–6 schede LoRa come relay per gli **avvisi**, rete locale o SSD scolastico autorizzato per i PDF, docente che confronta effettivamente estratti e pagine. Registrare tempi fino a revisione, digest inviati/recuperati e ricevute applicative, non copertura radio senza misure. Materiali dimostrativi inventati o con licenza; evitare libri protetti non redistribuibili e documenti degli studenti. Conservare solo il minimo di metadati di revisione; accessi alle fonti secondo autorizzazioni.

## Non duplicazione

**UC-099** riguarda ingestion/OCR derivati, **UC-136** ricerca di riferimenti mancanti, **UC-186** conflitti fra claim, **UC-149** cambio dello stato delle fonti e **UC-288** parità di traduzioni STEM. **UC-296 introduce una verifica distinta: l'ancora pagina/estratto deve continuare a provare il claim proprio nella versione esatta del PDF, oppure degradare esplicitamente e chiedere nuova revisione.** Non certifica automaticamente la verità del contenuto.