# POLLICINO — percorso didattico 2026/2027

POLLICINO usa la costruzione di un compressore lossless byte-level come filo conduttore per collegare informazione, probabilità, machine learning, Transformer e metodo sperimentale.

**Domanda annuale:** *come possiamo inviare meno bit e ricostruire esattamente lo stesso file?*

Il percorso ufficiale importabile in 2cornot2c è `course/pollicino-quarto-2026/bundle.json`. Ogni lezione viene mantenuta su due livelli sincronizzati: `handouts/` per gli studenti e `materials/` per il docente/approfondimento scientifico. Le attività tracciabili sono in `activities/`.

## Mappa del corso

| UDA | Tema | Lezioni |
|---|---|---:|
| 1 | Informazione, bit, probabilità ed entropia | 4 |
| 2 | Compressione come predizione | 5 |
| 3 | Dalla statistica alle reti neurali | 5 |
| 4 | Costruire un Transformer | 5 |
| 5 | Byte language model con PyTorch e MLX | 5 |
| 6 | Codec POLLICINO e ricerca sperimentale | 5 |

## Lezioni

### UDA 1 — Informazione, bit, probabilità ed entropia
1. Dal file ai bit e ai byte
2. Hash, collisioni e principio dei cassetti
3. Probabilità e quantità di informazione
4. Entropia di Shannon e baseline uniforme

### UDA 2 — Compressione come predizione
1. Ridondanza e Run-Length Encoding
2. Huffman e codici a prefisso
3. Dalle frequenze alle probabilità empiriche
4. Contesto, n-gram e modelli di Markov
5. Cross-entropy e bits-per-byte come metrica comune

### UDA 3 — Dalla statistica alle reti neurali
1. Dal punteggio al logit: un neurone come funzione parametrica
2. Softmax: da 256 logits a una distribuzione
3. Cross-entropy, gradiente e discesa del gradiente
4. Embedding: imparare una rappresentazione dei byte
5. Primo modello neurale next-byte: embedding + MLP

### UDA 4 — Costruire un Transformer
1. Sequenze, contesto causale e posizione
2. Self-attention: query, key e value
3. Maschera causale e previsione autoregressiva
4. Multi-head attention, residual, normalization e feed-forward
5. Tiny Transformer byte-level completo

### UDA 5 — Byte language model con PyTorch e MLX
1. Dataset byte-level, split e batch
2. Reference implementation e training loop in PyTorch
3. Validation, overfitting e scelta del checkpoint
4. Portare il byte model in MLX
5. Benchmark PyTorch/MLX e scheda esperimento

### UDA 6 — Codec POLLICINO e ricerca sperimentale
1. Dal modello probabilistico al range coder
2. Encoder/decoder deterministico e round-trip byte-perfect
3. Benchmark reale: payload, header, modello e baselines
4. Ablation, controlli e riproducibilità scientifica
5. POLLICINO Challenge: dal prototipo al report di ricerca

## Principi didattici

- Ogni idea matematica deve rispondere a una domanda concreta di programmazione o compressione.
- Prima si costruisce o si osserva un caso piccolo, poi si introduce l'astrazione del framework.
- La metrica comune del percorso è la probabilità assegnata al byte corretto, trasformata quando utile in negative log-likelihood e bits-per-byte.
- Un risultato di compressione è valido solo se il decoder ricostruisce esattamente l'input.
- Train, validation e test hanno ruoli distinti; le conclusioni devono essere proporzionate ai dati osservati.
- PyTorch e MLX sono backend di una stessa specifica concettuale, non due corsi separati.

## Stato editoriale

La versione `0.2.0` è una **bozza completa del percorso annuale**. È intenzionalmente progettata per essere rifinita durante il corso: esempi, durata, esercizi, figure, riferimenti e rubriche possono cambiare mantenendo stabili gli ID di UDA e lezioni.

Vedi `pollicino-quarto-2026/AUTHORING.md` per il contratto di sincronizzazione tra versione studenti e versione docente.
