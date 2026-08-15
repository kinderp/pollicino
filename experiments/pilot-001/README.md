# PILOT-001 — POLLICINO self-corpus

Primo esperimento scientifico riproducibile di POLLICINO.

## Domanda

Quanto del gap tra cross-entropy del ByteTransformer e dimensione finale di un file lossless dipende da:

1. qualità predittiva del modello;
2. quantizzazione delle probabilità in una CDF intera;
3. arithmetic/range coder;
4. header e metadati del container `.pol`?

## Dataset congelato

`pollicino-self-v1` è costruito **direttamente dal checkout Git** del parent commit `6a65aa6...` usando `prepare_data.py`. Include UDA 5, UDA 6, `src/pollicino`, `docs/research`, il manifest del corso e `pyproject.toml`.

È un corpus reale ma **domain-specific e self-referential**: non misura ancora la compressione universale.

| split | file | byte | SHA-256 |
|---|---:|---:|---|
| train | 66 | 120539 | `eeeb4d5b...c52e8` |
| validation | 7 | 14256 | `0b4304b2...f69b8` |
| test | 9 | 12711 | `3ac9c682...8a33` |

La divisione è per file: `sha256(path) mod 100`, con 0–79 train, 80–89 validation, 90–99 test.

## ModelSpec

```text
vocab_size       256
context_length    32
d_model           32
n_heads            4
n_layers           2
d_ff              64
parameters     34816
```

Training: PyTorch CPU, seed 1337, algoritmi deterministici, un thread CPU, AdamW, learning rate 0.003, batch 32, 300 step.

La validation usata durante il training scende da **8.0984 bpb** dopo il primo step a **3.9068 bpb** a step 300. Una valutazione successiva su una finestra validation più ampia dà **3.9862 bpb**; sul test split dà **3.4197 bpb**.

## Entropy-coding experiment

Il test di coding usa i primi **2048 byte** del test split.

| misura | bpb |
|---|---:|
| modello float | **3.1954** |
| CDF quantizzata | **3.2051** |
| payload range-coded | **3.2056** |
| `.pol` completo | **3.5664** |
| zlib | 2.9336 |
| gzip | 2.9805 |
| zstd -19 | 3.0234 |
| bz2 | 3.2773 |
| xz -9e | 3.3594 |

### Dove perdiamo bit?

```text
modello float           3.1954 bpb
        + quantizzazione 0.0097
CDF ideale              3.2051
        + range coder    0.0005
payload reale           3.2056
        + POL1 header    0.3608
file .pol               3.5664 bpb
```

Il coder è quindi quasi ideale rispetto alla CDF quantizzata. Il gap principale rispetto a zlib/gzip/zstd viene dalla **qualità predittiva** e, su file piccoli, dall'**header**.

## Risultato del pilot

POLLICINO non batte ancora i migliori baseline classici sullo slice scelto. Questo è un risultato utile: abbiamo localizzato il collo di bottiglia.

Il payload neurale è a 3.2056 bpb; il container finale è a 3.5664 bpb. La prossima fase deve quindi studiare:

- modelli più capaci e context più lungo;
- test slice più grandi per ammortizzare l'header;
- caching/KV-cache per accelerare encode/decode;
- più seed e più domini;
- parità CDF PyTorch↔MLX.

## Riproduzione

```bash
PYTHONPATH=src python experiments/pilot-001/prepare_data.py
PYTHONPATH=src python experiments/pilot-001/train.py
PYTHONPATH=src python experiments/pilot-001/evaluate.py
```

Il checkpoint del run originale non viene versionato in Git; `results.json` ne registra SHA-256 e dimensione. Una nuova esecuzione crea localmente `pilot-001-best.pt`.

## Limiti

- un solo seed;
- corpus interno al progetto;
- modello molto piccolo;
- CPU-only;
- nessuna parità PyTorch↔MLX;
- entropy-coding autoregressivo non ottimizzato e senza KV-cache;
- nessuna conclusione su immagini, audio, binari compressi, dati casuali o corpus esterni.
