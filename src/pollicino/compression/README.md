# Compression layer

POLLICINO converts integer next-byte distributions into a real lossless bitstream.

Current scope: 32-bit integer arithmetic/range coder; deterministic quantization to positive integer frequencies; `POL1` container with SHA-256 and model fingerprint; self-contained uniform/static-histogram modes; shared-model mode; PyTorch same-runtime CDF adapter; and deterministic causal adaptive n-gram providers.

A result is valid only after independent byte-perfect decode and SHA-256 verification.

## Adaptive coding

`AdaptiveNGramCDFProvider` builds order 0..N integer byte counts from the already decoded prefix. Encoder and decoder start from the same empty state, so no adaptive delta is transmitted. `NeuralPriorAdaptiveCDFProvider` optionally injects a fixed neural CDF as pseudo-count prior while file-local counts progressively dominate it.

The adaptive providers are deliberately integer/state-machine based: they do not perform online gradient updates and their state is a deterministic function of the reconstructed prefix. PILOT-005 evaluates this mechanism on Canterbury and Artificial Corpus inputs.

`shared-model` does not transmit neural weights. The current PyTorch fingerprint is canonical only inside PyTorch; PyTorch↔MLX cross-backend identity and exact CDF parity remain research milestones.

```bash
python -m pollicino.compression compress input.bin output.pol --mode static
python -m pollicino.compression inspect output.pol
python -m pollicino.compression restore output.pol restored.bin
```
