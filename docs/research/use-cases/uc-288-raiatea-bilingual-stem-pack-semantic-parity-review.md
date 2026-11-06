# UC-288 — Raiatea: lezioni STEM bilingui senza alterare codice, formule e riferimenti

**Stato:** proposta documentale del **6 novembre 2026**. Non implementata né testata; nessun risultato attribuito a un LLM. **Difficoltà alta.** Nessuna modifica al PHY LoRa congelato o a MAC, driver, firmware.

## Problema concreto

Una scuola prepara una scheda didattica italiana con esempi C/Python, espressioni matematiche, nomi di funzioni e riferimenti bibliografici. Un altro laboratorio disconnesso vuole un adattamento in inglese. Una traduzione generata automaticamente può modificare **letterali del codice, numeri, unità, comandi terminale, riferimenti a figure o termini tecnici**, rendendo la scheda inutilizzabile pur essendo grammaticalmente fluida. Dobbiamo consegnare una *variante bilingue revisionata* e legata alla versione esatta del materiale sorgente, distinguendo controlli automatici da approvazione didattica umana.

**Scenario Messina:** una lezione su puntatori C o reti in un laboratorio di Messina viene richiesto da una classe a Rometta; revisioni e correzioni arrivano attraverso relay fra Villafranca, Rometta e Venetico in tempi differenti. FSL: gli studenti implementano il validatore e le fixture; la decisione di qualità rimane del docente.

## Attori e perché PollicinoNet

Docente autore, traduttore umano o LLM locale facoltativo, validatore deterministico, revisore italiano/inglese, Raiatea corpus e cache, studenti con relay store-and-forward. LoRa permette discovery e stato della revisione; non bisogna caricare un intero PDF sulla radio. Un pacchetto `source_hash`, `target_lang`, `variant_hash`, `review_state`, `review_epoch` rimane utile anche quando testo e review si incontrano più tardi.

## Bearer e identità

- **LoRa:** richiesta di variante, identificativi/digest e revoca di approvazione in forma compatta; nessun file esteso.
- **BLE:** bozza di testo breve, glossario o proof vicino.
- **Wi-Fi/LAN/Internet:** Markdown/HTML/PDF, diff, test di codice e manifest completo; Internet solo se autorizzato.
- **USB/SSD/trasporto fisico:** pack intero cifrato con checksum a ricevente offline.
- **DISCOVERY:** variante disponibile o richiesta; **EXACT:** hash sorgente/derivato + test di blocchi immutabili; **SEMANTIC:** equivalenza dei concetti **solo dopo revisione umana**, non dal solo hash.

Record di esempio: `source_hash`, `source_version`, `target_lang=it|en`, `protected_blocks[]`, `glossary_version`, `variant_hash`, `code_tests_report_hash`, `reviewer_role`, `approval_signature?`, `status=DRAFT|AUTO_CHECKED|NEEDS_REVIEW|APPROVED|REJECTED|STALE`. L'assenza di approvazione non significa «approvato». Distinguere formattazione e caratteri da codice semanticamente verificato: serve hash sui blocchi immutabili, parser e test appropriati.

## Software immediato (da implementare)

1. Preparare un testo *originale e autorizzato* con un esempio C/Python eseguibile, pseudocodice, formula `2 * (n + 1)`, unità e due citazioni fittizie; creare varianti italiane/inglesi controllate.
2. Iniettare errori: `n+1` diventa `n-1`, `<=` diventa `<`, `printf` cambia, variabile viene rinominata, comando shell diverso, link inesatto, termine didattico ambiguo, paragrafo omesso.
3. Applicare controlli automatici **solo** su ciò che possono verificare: identità dei blocchi protetti, parse/compilazione dove pertinente, test di snippet in sandbox senza accesso rete, conteggio e collegamento di formule, ID bibliografici, versione e lingua dichiarata.
4. Richiedere revisione docente del senso e della progressione educativa, salvare motivazioni della correzione. Un `AUTO_CHECKED` non passa a `APPROVED` senza firma di revisore autorizzato.
5. Simulare partizione e ricezione ritardata: la versione sorgente cambia dopo l'approvazione di una traduzione; marcare il derivato `STALE`, non distribuirlo come approvato per la nuova sorgente.
6. Restituire rapporto riproducibile `PASS/FAIL/UNKNOWN` con conteggi di blocchi, errori intenzionali rilevati e falsi negativi; nessun LLM deve essere necessario nel test iniziale.

**Accettazione:** (A) errore aritmetico e alterazione del codice bloccano la variante; (B) bozze non firmate non sono presentate come lezioni approvate; (C) variazione di source hash invalida il vecchio stato per la versione nuova; (D) se citazione o legame di sorgente non è verificabile, dichiarare `UNKNOWN`; (E) l'assenza di rete non può aggirare le policy sui materiali.

## Prova fisica

Due PC isolati con cache Raiatea, un docente revisore e 4–6 schede LoRa per annunci compatti. Pubblicare una lezione propria sintetica a Rometta e inoltrare richiesta/approvazione via uno o due relay fino a un secondo checkpoint; trasferire la variante integrale tramite BLE/Wi-Fi o chiavetta, ricontrollare hash e stato nel punto di destinazione, poi simulare la revisione tardiva. Annotare misure reali soltanto dopo la prova: tempo fra richiesta e variante approvata, byte per bearer, errori rilevati, esito verificato del destinatario. Non attribuire a LoRa byte spediti per Wi-Fi/USB.

## Sicurezza/privacy e difficoltà

Solo contenuti didattici originali o concessi in licenza; nessun compito personale, PEI/PDP o dati degli alunni. Le traduzioni automatiche e i contenuti da cache non sono istruzioni da eseguire (UC-246). Caricamento solo di artefatti verificati, review autorizzata, revoche ed epoche esplicite, niente upload di materiali riservati a servizi cloud non autorizzati. **Alta** perché la correttezza tecnica testabile non prova l'equivalenza pedagogica.

## Anti-duplicazione e riferimenti

**UC-106** riguarda bollettini di emergenza multilingue firmati (fonte autorevole); **UC-192** pack didattici accessibili e reading order; **UC-006/099/120** versioni/derivati Raiatea; **UC-237** accettazione SDD; **UC-258** falsa corroborazione di risposte generate. **UC-288 introduce la verifica automatica degli invarianti STEM + revisione bilingue umana** specifica per lezioni didattiche, preservando codice/formule/riferimenti in un derivato asincrono.

Strumenti di riferimento: [W3C Internationalization Checker](https://validator.w3.org/i18n-checker/) per aspetti verificabili di lingua/markup, [HTML `translate`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/translate) per marcare porzioni che non devono essere tradotte. Nessuno dei due certifica correttezza didattica.
