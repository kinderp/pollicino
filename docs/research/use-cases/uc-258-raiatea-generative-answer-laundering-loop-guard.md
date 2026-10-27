# UC-258 — Antiriciclaggio delle risposte generate e controllo dei cicli Raiatea

**Stato:** proposta documentale del 27 ottobre 2026, non implementata. **Difficoltà:** alta (provenienza, grafo e verifica delle risposte).

## Problema e user story

Tre scuole disconnesse usano Raiatea con modelli locali. La scuola A genera un riassunto e lo salva. B riceve il riassunto, lo indicizza come se fosse una fonte originale e genera un'altra risposta. C riceve entrambe le risposte e le cita come **due fonti indipendenti**, benché derivino dal medesimo documento — o, peggio, si citino a vicenda. La ripetizione di un'affermazione può sembrare corroborazione.

**User story:** come docente che consulta Raiatea offline, voglio sapere se una risposta poggia su **fonti originali verificabili** oppure su altre risposte generate, ed evitare che catene circolari o copie della stessa origine aumentino artificialmente la fiducia.

Non è necessario che una risposta sia malevola o inesatta: è sufficiente che perda la propria genealogia durante le sincronizzazioni differite.

## Attori / nodi

Editore del documento originale, 2–3 cache Raiatea scolastiche, worker RAG/LLM locale, motore di provenienza, revisore umano, nodi relay PollicinoNet, gateway opzionale. Per una dimostrazione: corpora di dispense pubbliche o sintetiche diversi in tre laboratori fra Messina, Rometta e Venetico.

## Perché PollicinoNet

Con store-and-forward **un derivato può arrivare prima dell'originale**, e una risposta può essere riutilizzata da più nodi che non possono controllare immediatamente i riferimenti. Devono quindi viaggiare anche piccole prove di origine e stato, e l'applicazione deve rendere visibile la differenza fra VERIFIED_SOURCE_ANCHORED, UNRESOLVED_SOURCE, DERIVATIVE_ONLY, CYCLE_DETECTED, POLICY_BLOCKED.

Grafo minimo di provenienza (contratto applicativo proposto):

    artifact_id, artifact_hash, artifact_kind (SOURCE|EXTRACT|ANSWER),
    derived_from_hashes[], exact_evidence_refs[], model_version,
    corpus_version, transform_id, reviewer_status, permissions,
    graph_digest, verification_epoch

Ogni risposta mantiene un insieme di **radici documentali uniche**, raggiunte attraversando gli archi dei derivati; due riassunti della medesima radice non costituiscono due fonti indipendenti. Un grafo chiuso senza fonte primaria o con cicli è un risultato insufficiente, non un fatto confermato. Integrità crittografica e firma provano origine dei byte, **non verità semantica**.

- **DISCOVERY:** digesti di grafo e riferimenti di fonti mancanti.
- **EXACT:** ID, versioni, hash, relazioni di derivazione e policy.
- **SEMANTIC:** risposta con etichette di attendibilità epistemica verificabili dalla provenienza, non percentuali di verità inventate.

## Bearer

- **LoRa:** piccoli ID/digest, richiesta di radici mancanti e stati di verifica, soltanto nei limiti radio misurati.
- **BLE:** inventari e metadati di provenienza brevi fra due cache.
- **Wi-Fi/LAN/Internet:** testi, fonti complete, grafi e indici; Internet solo se disponibile.
- **USB/SSD / trasporto fisico:** corpora e grafi maggiori, previa verifica di hash, licenze e autorizzazioni.

## Esperimenti software subito eseguibili

Tre processi Raiatea simulati, cinque testi sorgente sintetici e un insieme di risposte simulate (non richiede un modello LLM per il primo test):

1. A crea risposta R1 da S1. B crea R2 da R1. C deve contare **una sola radice S1**, non due fonti.
2. Una risposta derivata R3 arriva prima di S1: stato UNRESOLVED_SOURCE e richiesta della fonte; niente citazione verificata finché manca l'evidenza.
3. Archi R4->R5->R4: rilevazione del ciclo, niente falsa attribuzione a documento originale.
4. S1 viene corretto o ritirato: risposte dipendenti passano a REASSESS_REQUIRED (integrazione UC-120/149).
5. Due documenti realmente indipendenti S1 e S2 supportano la stessa proposizione: due radici *distinte*, ma la loro indipendenza editoriale rimane da verificare, non è garantita dagli hash.
6. Fonte autentica ma istruzioni avversarie: nessuna promozione a istruzione per il modello (UC-246).
7. Permesso di ridistribuzione mancante: il grafo può conservare un riferimento opaco, ma non esportare i testi protetti.
8. Un importatore che elimina derived_from_hashes deve essere rifiutato o quarantinato, non considerato nuova fonte.

**Invarianti:** zero risposte generate promosse automaticamente a sorgente primaria nei test deterministici; zero cicli etichettati come prova; riferimenti inesistenti espliciti; nessuna garanzia automatica sulla correttezza del contenuto. Misurare rilevamenti di ciclo, radici risolte/mancanti, false indipendenze, byte dei digest e tempi simulati.

## Prova fisica nella rete scolastica

Due o tre PC isolati, 4–6 relay LoRa; introdurre deliberatamente R2 prima di S1 in un laboratorio e verificare che l'interfaccia mantenga UNRESOLVED_SOURCE. Trasportare successivamente il manifest delle radici via LoRa, il contenuto di S1 via Wi-Fi/USB, e verificare la riconciliazione. Confrontare l'ordine effettivo di arrivo, byte trasferiti per bearer e tempi fra arrivo/deliberazione applicativa. Nessuna pretesa di performance LoRa senza TX/RX e contatti misurati.

## Privacy e sicurezza

Solo documenti pubblici, licenziati o sintetici; nessuna domanda personale o credenziale in broadcast. Firmare i manifest di provenienza senza fidarsi del solo nome del file; limitare query private, hash di contenuti potenzialmente identificativi e log; rispettare ritiri/licenze. Evitare il trasferimento pubblico di passaggi protetti da copyright. Le politiche di revisione umana rimangono esplicite.

## Novità rispetto al catalogo

**UC-046** genera risposte con citazioni; **UC-099** registra la pipeline di indicizzazione; **UC-120/149** invalidano derivati e fonti cambiate; **UC-186** gestisce contraddizioni di proposizioni; **UC-246** difende dal prompt injection nei documenti. **UC-258 impedisce il salto di autorità da risposta generata a fonte indipendente e la falsa corroborazione attraverso derivati/cicli fra cache offline.** Non è un nuovo motore RAG: è un controllo di provenienza per il riuso delle risposte.

Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware radio.
