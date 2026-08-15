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

## UDA operative

### UDA 1 — fondamenta dell'informazione
Dalla versione `0.3.0`, le quattro activity della UDA 1 includono starter Python, fixture, test pubblici, test nascosti, soluzioni docente e notebook comune.

### UDA 2 — compressione come predizione
Dalla versione `0.4.0`, anche le cinque activity della UDA 2 sono eseguibili end-to-end:

- RLE con codec reale e round-trip;
- Huffman canonico con payload bit-packed e stima del costo del codebook;
- modello zero-order con entropia, cross-entropy e smoothing;
- n-gram/Markov con train/test separati e contesti mai visti;
- benchmark uniforme/0-gram/1-gram/2-gram/3-gram in bits-per-byte.

Il notebook comune è `notebooks/uda-02/pollicino-uda02-lab.ipynb`.

Tutti i laboratori delle UDA 1 e 2 usano esclusivamente la libreria standard Python:

```bash
python -m unittest discover -s tests -v
```

## Principi didattici

- Ogni idea matematica deve rispondere a una domanda concreta di programmazione o compressione.
- Prima si costruisce un caso piccolo, poi si introduce l'astrazione del framework.
- La metrica comune è la probabilità del byte corretto trasformata in negative log-likelihood e bits-per-byte.
- Un risultato lossless è valido solo se il decoder ricostruisce esattamente l'input quando esiste un encoder.
- Train, validation e test hanno ruoli distinti.
- PyTorch e MLX sono backend della stessa specifica concettuale.

## Stato editoriale

La versione `0.4.0` mantiene la bozza completa delle 29 lezioni annuali e rende operative end-to-end le UDA 1 e 2. Contenuti ed esempi possono essere raffinati durante il corso mantenendo stabili gli ID.

Vedi `pollicino-quarto-2026/AUTHORING.md` per il contratto di sincronizzazione.
