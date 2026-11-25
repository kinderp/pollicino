# UC-342 — Raiatea: formule accessibili con significato verificato fra notazione e lettura vocale

**Stato: 25 novembre 2026, proposta documentale, non implementata né testata. Difficoltà medio-alta/alta. PHY LoRa congelato, MAC, driver e firmware invariati.**

## Problema, attori e scenario
Due formule possono avere aspetto molto simile ma significato diverso. Una lettura vocale generata da AI può omettere parentesi o confondere una coordinata con un intervallo aperto. Ad esempio -(x^2) e (-x)^2 non sono generalmente equivalenti; (3,6) può essere una coppia ordinata oppure un intervallo aperto, a seconda del contesto. Una dispensa con formule graficamente corrette non è perciò automaticamente accessibile.

Docente di matematica/informatica, autore, lavoratore locale MathML/AI opzionale, Raiatea, revisore docente, verificatore di accessibilità, cache scolastiche e relay volontari. Un laboratorio a Milazzo prepara formule originali; uno a Venetico elabora una variante HTML/MathML e uno a Rometta riceve la revisione anche offline. Nessuna connessione radio fra sedi è assunta.

## Perché PollicinoNet
Le richieste e lo stato di revisione possono essere trasportati con pochi byte; sorgente, albero matematico, rendering e prove di lettura possono arrivare separatamente. Una correzione deve invalidare le approvazioni legate alla versione precedente.
- LoRa: ID opachi della revisione, richiesta di correzione, digest e stato; non intere formule complesse o audio.
- BLE: piccolo manifest o diff locale; Wi-Fi/LAN/Internet: pacchetto HTML/MathML/LaTeX e report del renderer; USB/SSD/trasporto fisico: pacchetto verificato in assenza di rete.
- DISCOVERY: formula o variante disponibile; EXACT: hash sorgente, struttura e versione di ogni derivato e profilo di prova; SEMANTIC: descrizione del significato revisionata, non prova di equivalenza.

FormulaPack={source_hash, formula_id, source_context_hash, notation_tree_hash, mathml_hash, intent_spec_version, expected_meaning, speech_locale, renderer_version, review_state, evidence_hash}. Stati DRAFT, STRUCTURE_CHECKED, NEEDS_REVIEW, APPROVED_FOR_PROFILE, REJECTED, STALE. Non garantire accessibilità universale sulla base di un solo reader. MathML 4, ancora riferimento in evoluzione, documenta gli attributi intent e arg per disambiguare la notazione: https://www.w3.org/TR/2026/WD-mathml4-20261027/ ; dimostrazione W3C: https://www.w3.org/2022/09/TPAC/demos/math-a11y.html . Il supporto effettivo dipende da renderer/tecnologia assistiva e versione.

## Software subito (piano, non eseguito)
Creare 20 formule originali con albero sintattico atteso e descrizione italiana revisionabile; includere raggruppamenti, frazioni annidate, potenze, meno unario, matrice trasposta, intervallo/coppia e unità. Usare un sottoinsieme esplicito di LaTeX/MathML, parser XML sicuro e confronti deterministici dei nodi rilevanti. Non assumere equivalenza simbolica generale. Iniettare 10 varianti errate: parentesi mancanti, numeratore/denominatore scambiati, intent incompatibile, esponente mal interpretato, testo vocale ambiguo e revisione vecchia.
Simulare partizioni e arrivi tardivi di correzioni; verificare che i pacchetti approvati per vecchio hash siano STALE rispetto al nuovo.
Gate: nessuna variante con divergenza nota può essere APPROVED; controlli automatici distinguono CHECKED da revisione umana; profili non supportati restano UNKNOWN/NEEDS_REVIEW; il caso ambiguo (3,6) richiede contesto; non eseguire markup o istruzioni incorporate. Metriche software: errori riconosciuti, falsi negativi, bozze bloccate e corrispondenza tra profili.

## Hardware e prova reale
3–4 schede LoRa, due PC con browser e lettore di schermo, eventuale display braille se disponibile e testato separatamente. Docente e adulto volontario competente verificano lettura e navigazione delle formule per almeno due profili, con versione precisa. Nessun profilo personale di alunni, nessuna certificazione di accessibilità, non assumere equivalenza tra speech e braille. Trasportare manifest e revisioni su LoRa e file su Wi-Fi/USB: rilevare ricevute e tempi effettivi separatamente da qualità della formula.

## Privacy/sicurezza
Contenuti originali o autorizzati, niente PEI/PDP o dati di disabilità. MathML e output AI sono dati non fidati: parser senza entità esterne, no script o URL attivi, niente istruzioni nascoste nel testo vocale. Approvazioni firmate su hash esatto e profilo di test. Nessun uso di una bozza non verificata in una prova valutativa.

## Anti-duplicazione
UC-192 prepara pacchetti accessibili in generale (include formule), UC-288 preserva formule durante traduzione bilingue, UC-296 lega citazioni a versioni, UC-332 preserva scala di immagini. Qui si verifica la **disambiguazione semantica di una singola espressione fra albero, rappresentazione visiva e lettura assistiva**, con gate specifico per profilo e contesto. È una specializzazione dichiarata di UC-192, non una nuova funzione generale di conversione.
