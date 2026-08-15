# POLLICINO — percorso didattico 2026/2027

POLLICINO usa la costruzione di un compressore lossless byte-level come filo conduttore per collegare informazione, probabilità, machine learning, Transformer e metodo sperimentale.

**Domanda annuale:** *come possiamo inviare meno bit e ricostruire esattamente lo stesso file?*

Il percorso ufficiale importabile in 2cornot2c è `course/pollicino-quarto-2026/bundle.json`. Ogni lezione mantiene activity machine-readable, handout studenti e materiale docente/scientifico.

## Mappa del corso

| UDA | Tema | Lezioni | Stato operativo |
|---|---|---:|---|
| 1 | Informazione, bit, probabilità ed entropia | 4 | laboratorio completo |
| 2 | Compressione come predizione | 5 | laboratorio completo |
| 3 | Dalla statistica alle reti neurali | 5 | laboratorio completo |
| 4 | Costruire un Transformer | 5 | laboratorio completo |
| 5 | Byte language model con PyTorch e MLX | 5 | laboratorio completo |
| 6 | Codec POLLICINO e ricerca sperimentale | 5 | teoria/bozza |

## UDA 4 — il Transformer non è magia

La UDA 4 resta volutamente **senza framework ML** e costruisce il forward pass a mano:

```text
byte + posizione
-> Q/K/V
-> scaled dot-product attention
-> causal mask
-> multi-head attention
-> RMSNorm + residual
-> feed-forward
-> Tiny Byte Transformer
-> 256 logits
```

Il test più importante è il **future-leakage test**: cambiare il futuro non deve modificare gli output del prefisso. Il Tiny Transformer didattico finale ha 4.696 parametri nella configurazione di riferimento e, prima dell'addestramento, resta vicino alla baseline uniforme di 8 bit/byte.

L'addestramento del Transformer non viene duplicato qui: passa alla UDA 5, dove la stessa architettura sarà implementata in PyTorch e MLX.

## UDA 5 — due backend, una specifica

La UDA 5 introduce PyTorch e MLX solo dopo aver costruito manualmente il Transformer. PyTorch usa `nn.Module`, cross entropy e `AdamW`; MLX usa `nn.Module`, `nn.value_and_grad`, `optim.AdamW` e `mx.eval`. La stessa ModelSpec e la stessa metrica `bpb = loss_nats / ln(2)` permettono un confronto riproducibile senza pretendere identità numerica tra backend.

La ModelSpec di riferimento è condivisa anche dal track scientifico in `src/pollicino/model_spec.py`, con implementazioni parallele in `src/pollicino/backends/pytorch/` e `src/pollicino/backends/mlx/`.

## Principi didattici

- Ogni astrazione viene costruita prima in piccolo.
- Shape, causalità e probabilità sono invarianti verificati dai test.
- `1/sqrt(d_k)` e softmax stabile sono parte dell'algoritmo, non dettagli cosmetici.
- La causal mask è un requisito di correttezza: un modello che vede il futuro falsa loss e bpb.
- Train, validation e test hanno ruoli distinti.
- PyTorch e MLX sono backend della stessa specifica, non due modelli diversi.

## Stato editoriale

La versione `0.7.0` rende operative end-to-end le UDA 1–5. Esempi, tempi e rubriche restano rifinibili mantenendo stabili gli ID.
