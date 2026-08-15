# Compression layer

POLLICINO converts integer next-byte distributions into a real lossless bitstream.

Current v1 scope: 32-bit integer arithmetic/range coder; deterministic quantization to positive integer frequencies; `POL1` container with SHA-256 and model fingerprint; self-contained uniform/static-histogram modes; shared-model mode; PyTorch same-runtime CDF adapter.

A result is valid only after independent byte-perfect decode and SHA-256 verification.

`shared-model` does not transmit weights. The current PyTorch fingerprint is canonical only inside PyTorch; PyTorch↔MLX cross-backend identity and exact CDF parity remain research milestones.

```bash
python -m pollicino.compression compress input.bin output.pol --mode static
python -m pollicino.compression inspect output.pol
python -m pollicino.compression restore output.pol restored.bin
```
