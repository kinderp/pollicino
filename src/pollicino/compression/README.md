# Compression layer

This package will contain deterministic entropy-coding components.

The first real codec target is a range/arithmetic coder driven by quantized next-byte probability distributions. Encoder and decoder must derive **exactly the same integer coding distribution at every step**.

Later experiments may add candidate enumeration and short-fingerprint identification. Any fingerprint bits required by the decoder are counted as payload, and final output is independently verified with a full-file cryptographic hash.
