# POLLICINO Research Questions

## RQ1 — Prediction and realized compression

How closely does validation cross-entropy predict realized lossless compressed size after finite-precision entropy coding?

## RQ2 — Context and model capacity

How do context length and parameter count affect bits-per-byte across file domains, and where do diminishing returns begin?

## RQ3 — Universal versus domain-specific models

When does one shared byte model outperform domain-specific models after checkpoint distribution and amortization are included?

## RQ4 — Shared-model amortization / MDL

How much data must reuse a learned model before total description length becomes competitive with classical compressors?

## RQ5 — PyTorch / MLX parity

For equivalent model specifications, how do PyTorch and MLX compare in convergence, throughput, peak memory and reproducibility?

## RQ6 — Model scaling versus compression gain

Does improved next-byte modeling continue to translate into useful compression gains as the model grows, once model cost and decode compute are included?

## RQ7 — Generative identification

Can a learned distribution narrow an exact candidate space enough that a short fingerprint plus search is useful for lossless reconstruction?

## RQ8 — Fingerprint length versus search cost

What relationship exists between transmitted fingerprint/residual bits, the number of candidates considered and decoder compute?

## RQ9 — Bandwidth / compute Pareto frontier

Are there useful Pareto-optimal regimes where extra reconstruction compute meaningfully reduces transmitted information compared with ordinary entropy coding?

## RQ10 — Hybrid coding

Can a chunk-level policy improve total description length by choosing among content-address references, learned entropy coding, classical coding and raw residual transmission?

## RQ11 — Negative controls

Do random, encrypted and already-compressed data behave as theory predicts, and can they expose leakage or accounting errors in the experimental pipeline?
