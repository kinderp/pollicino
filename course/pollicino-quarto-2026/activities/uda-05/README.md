# UDA 5 — Byte language model con PyTorch e MLX

Questa UDA prende il Tiny Transformer costruito a mano nella UDA 4 e lo trasforma in un modello addestrabile con due backend reali.

Principio di parità:

```text
stesso corpus + stesso split + stessa ModelSpec + stessa metrica bpb
                     ↓
             PyTorch     MLX
```

PyTorch è il backend di riferimento scientifico e CUDA/MPS. MLX è il backend Apple Silicon. I risultati numerici non devono coincidere bit per bit: devono però descrivere la stessa architettura e lo stesso protocollo sperimentale.

La metrica comune resta:

`bpb = cross_entropy_nats / ln(2)`.

I checkpoint, i seed, l'hardware e le versioni dei framework fanno parte del risultato sperimentale.
