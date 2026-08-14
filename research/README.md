# POLLICINO — Research Track

This directory is the entry point for the scientific version of POLLICINO.

The executable research code lives under `src/pollicino/`; this directory will hold research plans, experiment series and manuscript-oriented material that should remain separate from the classroom path.

## Backend strategy

One mathematical model specification, two implementations:

```text
                  YAML ModelSpec
                       |
              +--------+--------+
              |                 |
           PyTorch             MLX
              |                 |
              +--------+--------+
                       |
            identical evaluation
                       |
              bits/byte + codec
```

- **PyTorch** is the reference backend for portability, CUDA and future multi-GPU scaling.
- **MLX** is the Apple-Silicon backend for local research and unified-memory experiments.

## First experimental ladder

```text
uniform
  -> empirical byte frequency
  -> bigram
  -> n-gram / Markov
  -> MLP
  -> RNN / GRU
  -> tiny byte Transformer
  -> scaled byte Transformer
```

Each step must justify its complexity by measurable predictive or coding gains.

## Primary metrics

- validation cross-entropy,
- theoretical bits/byte,
- realized coded bits/byte,
- checkpoint size,
- amortized total description length,
- encode/decode throughput,
- peak memory,
- exact round-trip correctness.

See `docs/research/questions.md` and `docs/research/protocol.md` for the current research questions and mandatory experiment metadata.
