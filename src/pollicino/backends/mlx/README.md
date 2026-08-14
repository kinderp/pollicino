# MLX backend

Apple-Silicon backend for POLLICINO. It mirrors the PyTorch architecture from the same framework-independent model specification whenever practical.

Parity checks should cover:

- tensor shapes,
- parameter count,
- causal masking semantics,
- positional encoding,
- initialization policy,
- loss definition,
- checkpoint metadata,
- validation bits/byte.

The backend is also a research target: it lets us compare unified-memory Apple hardware with the PyTorch/CUDA path as the project scales.
