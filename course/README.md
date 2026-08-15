# POLLICINO — percorso didattico 2026/2027

POLLICINO usa la costruzione di un compressore lossless byte-level come filo conduttore per collegare informazione, probabilità, machine learning, Transformer e metodo sperimentale.

**Domanda annuale:** *come possiamo inviare meno bit e ricostruire esattamente lo stesso file?*

Il bundle importabile in `2cornot2c` è `course/pollicino-quarto-2026/bundle.json`.

| UDA | Tema | Lezioni | Stato operativo |
|---|---|---:|---|
| 1 | Informazione, bit, probabilità ed entropia | 4 | laboratorio completo |
| 2 | Compressione come predizione | 5 | laboratorio completo |
| 3 | Dalla statistica alle reti neurali | 5 | laboratorio completo |
| 4 | Costruire un Transformer | 5 | laboratorio completo |
| 5 | Byte language model con PyTorch e MLX | 5 | laboratorio completo |
| 6 | Codec POLLICINO e ricerca sperimentale | 5 | laboratorio completo |

```text
bit -> probabilità -> entropia -> n-gram -> rete neurale
-> attention -> Transformer -> training PyTorch/MLX
-> CDF intera -> range coder -> file .pol -> round-trip SHA-256
```

UDA 6 distingue sempre bpb teorico, payload arithmetic-coded e dimensione completa del file `.pol`. `shared-model` trasporta un fingerprint, non i pesi: costo del modello e ammortamento devono essere dichiarati. La parità esatta PyTorch↔MLX delle CDF resta una domanda di ricerca finché non viene dimostrata.

La versione `0.8.0` rende operative end-to-end tutte le 29 lezioni.
