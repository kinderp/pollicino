# UC-305 — Raiatea: non interrogare un indice semantico con embedding incompatibili

**Stato (12 novembre 2026):** proposta documentale, test non eseguiti, nessuna misura radio. Difficoltà **alta**. PHY LoRa, MAC, driver e firmware invariati.

## Problema concreto
Tre laboratori mantengono indici Raiatea aggiornati in momenti differenti. Uno indicizza una raccolta con un modello di embedding A, un altro usa B, e un terzo cambia il preprocessing o il prompt `query/document`. Anche se due vettori hanno lo **stesso numero di componenti**, potrebbero non avere significato confrontabile. Un cercatore che confronta direttamente i punteggi può restituire riferimenti apparentemente convincenti ma sbagliati.

**Domanda misurabile:** l'applicazione riesce a **rifiutare confronti vettoriali incompatibili prima della ricerca**, spiegare il motivo, e trovare un fallback utile senza inventare citazioni?

## Attori e scenario scolastico
Docenti/revisori, tre PC o Raspberry Pi con corpora pubblici di prova, worker di embedding, un query node Raiatea, checkpoint PollicinoNet, 4–6 relay virtuali/LoRa e un verificatore. Scenario sintetico: Rometta conserva un corpus di informatica, Venetico una copia aggiornata e Villafranca una ricerca con un profilo differente. Non si presume che questi luoghi siano collegati via LoRa.

## Perché PollicinoNet
La disponibilità dei metadati di un indice e quella dei suoi gigabyte non devono coincidere. PollicinoNet può diffondere **un profilo verificabile dell'indice e del query encoder**, portare la richiesta al nodo che dispone della versione adatta e, più tardi, trasferire un fallback o un job di reindicizzazione tramite bearer ricco. L'oggetto restituito è verificato EXACT e gli estratti mantengono riferimenti alla fonte.

- **DISCOVERY:** indice disponibile, corpus/snapshot, profilo e capabilities, solo metadati autorizzati.
- **EXACT:** hash del modello/adapter, versione tokenizer/preprocessing, dimensione, metrica, normalizzazione, prompt query/document, snapshot e hash dell'indice.
- **SEMANTIC:** stato `COMPATIBLE`, `REINDEX_REQUIRED`, `LEXICAL_FALLBACK`, `UNKNOWN`, senza spacciare un punteggio per verità.

## Bearer
- **LoRa:** richiesta e risposta compattissima sul profilo se l'adapter le supporta; **mai vettori o PDF grandi**.
- **BLE:** piccoli manifest e discovery in presenza.
- **Wi-Fi/LAN/Internet:** indici, sorgenti, modelli approvati, log di valutazione, corpus.
- **SSD/USB/trasporto fisico:** indici e modelli voluminosi fra laboratori; validare il supporto/importazione (UC-294).

## Test software immediato (non eseguito)
Preparare **20 brevi brani pubblici o interamente sintetici**, **12 query con risposte attese create da un revisore** e **3 profili**. Prima eseguire un test deterministico con vettori artificiali: stesso numero di dimensioni ma basi diverse. Poi, come test facoltativo separato, usare 2 piccoli modelli di embedding locali con licenza compatibile. Combinare:
1. stesso encoder, stesso prompt/preprocessing/metrica;
2. encoder diverso a **dimensione identica** (incompatibile);
3. stesso encoder con normalizzazione/prompt/query processor differente;
4. indice sconosciuto/scaduto o non autorizzato.

Confrontare il gate `REJECT/UNKNOWN` prima del confronto semantico, fallback a ricerca lessicale autorizzata, e reindicizzazione *solo su consenso esplicito*. Misure: falsi `COMPATIBLE`, query rifiutate correttamente, recall@k sul piccolo gold standard, byte dei manifest, numero di citazioni effettivamente verificate. `same_dimension` **non** è un criterio sufficiente; anche un profilo combaciante non garantisce qualità della ricerca.

**Criteri di accettazione:** (1) incompatibilità dimostrata blocca punteggi vettoriali; (2) un profilo mancante produce `UNKNOWN`, non confronto ottimistico; (3) il fallback non è presentato come risultato vettoriale equivalente; (4) ogni risultato porta versioni e passaggio esatto della fonte; (5) nessuna citazione è `VERIFIED` solo perché semanticamente simile.

Schema minimo: `{query_id, corpus_snapshot_hash, index_hash, embedding_model_hash, tokenizer_profile, query_prompt_profile, document_prompt_profile, normalize, metric, dimension, access_policy, compatibility_verdict, source_refs}`.

## Hardware reale
Due/tre PC o Raspberry Pi con due indici di prova e **4 schede LoRa** per trasportare piccoli annunci/stati; Wi-Fi/USB per contenuti. Misurare solo allora tempo e byte end-to-end sui bearer realmente impiegati. Le prestazioni AI dipenderanno dal dispositivo e dal modello installato: nessun tempo di inferenza viene dato per misurato.

## Privacy e sicurezza
Indice/embedding possono contenere informazioni su documenti non pubblici: iniziare con corpora **pubblici o sintetici**, accesso verificato, nessuna ricerca su PDP, dati degli studenti o documenti riservati. Importazione in quarantena di indici e modelli, hash esatto e firma/autorizzazione. Non miscelare risultati di versioni o licenze differenti senza decisione esplicita.

## Anti-duplicazione
**UC-099** tratta la creazione di artefatti derivati, **UC-155** la fusione di shard *già compatibili*, **UC-065** la federazione di ricerche, **UC-120** l'invalidazione di derivati, **UC-296** la persistenza delle citazioni dopo una nuova versione PDF. **UC-305** verifica invece la **compatibilità di *ogni query* con l'indice remoto prima di confrontare vettori o punteggi**, includendo un fallback sicuro.

Riferimenti tecnici (nessuna prova delle prestazioni PollicinoNet):
- Sentence Transformers — ricerca semantica: https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
- Sentence Transformers — profili distinti `encode_query`/`encode_document`: https://www.sbert.net/docs/sentence_transformer/usage/usage.html
