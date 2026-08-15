# POLLICINO — percorso didattico 2026/2027

POLLICINO usa la costruzione di un compressore lossless byte-level come filo conduttore per collegare informazione, probabilità, machine learning, Transformer e metodo sperimentale.

**Domanda annuale:** *come possiamo inviare meno bit e ricostruire esattamente lo stesso file?*

Il percorso ufficiale importabile in 2cornot2c è `course/pollicino-quarto-2026/bundle.json`. Ogni lezione mantiene tre livelli sincronizzati: activity machine-readable, handout studenti e materiale docente/scientifico.

## Mappa del corso

| UDA | Tema | Lezioni | Stato operativo |
|---|---|---:|---|
| 1 | Informazione, bit, probabilità ed entropia | 4 | laboratorio completo |
| 2 | Compressione come predizione | 5 | laboratorio completo |
| 3 | Dalla statistica alle reti neurali | 5 | laboratorio completo |
| 4 | Costruire un Transformer | 5 | teoria/bozza |
| 5 | Byte language model con PyTorch e MLX | 5 | teoria/bozza |
| 6 | Codec POLLICINO e ricerca sperimentale | 5 | teoria/bozza |

## UDA 3 — dal modello statistico al modello neurale

La UDA 3 resta volutamente **senza framework ML**. Gli studenti costruiscono a mano:

```text
funzione affine -> logits -> softmax -> cross-entropy
-> gradiente -> embedding -> MLP next-byte
```

Ogni activity operativa usa starter Python, fixture, test pubblici, test nascosti e soluzione docente. Il notebook comune è `notebooks/uda-03/pollicino-uda03-lab.ipynb`.

Il quinto laboratorio contiene un piccolo MLP byte-level con embedding, hidden `tanh`, 256 logits e SGD/backprop manuale. L'obiettivo non è la velocità, ma rendere visibile ciò che PyTorch automatizzerà nella UDA 5.

## Principi didattici

- Ogni idea matematica deve rispondere a una domanda concreta di programmazione o compressione.
- Prima si costruisce o si osserva un caso piccolo, poi si introduce l'astrazione del framework.
- La metrica comune è la probabilità assegnata al byte corretto, trasformata in negative log-likelihood e bits-per-byte.
- Un risultato di compressione è valido solo se il decoder ricostruisce esattamente l'input.
- Train, validation e test hanno ruoli distinti.
- PyTorch e MLX sono backend di una stessa specifica concettuale, non due corsi separati.

## Stato editoriale

La versione `0.5.0` mantiene la bozza completa del percorso annuale e rende operative end-to-end le UDA 1–3. Esempi, durata, esercizi e rubriche restano volutamente rifinibili durante il corso, mantenendo stabili gli ID.
