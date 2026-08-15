# Exact CDF synchronization

Neural lossless coding requires `CDF_encoder(i,prefix) == CDF_decoder(i,prefix)` bit-for-bit at every position.

POLLICINO separates real-valued model probabilities from the actual coding contract: a deterministic quantizer maps probabilities to 256 strictly positive integer frequencies summing exactly to `2^precision_bits`; their cumulative sum is the CDF used by the coder.

Currently proven: integer range-coder round-trip; deterministic quantization; shared deterministic count-model round-trip; PyTorch same-runtime model-assisted round-trip; model fingerprint mismatch rejection.

Not yet proven: exact parity across PyTorch CPU/CUDA/MPS and MLX. Tiny floating-point differences near quantization boundaries can change one frequency and make decoding diverge. Cross-device and PyTorch↔MLX lossless parity is therefore a research milestone, not an assumption. Any correction bits required by a future synchronization protocol must be counted in compressed size.
