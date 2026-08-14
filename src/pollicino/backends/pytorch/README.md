# PyTorch backend

Reference scientific backend for portable research and future CUDA/multi-GPU scaling.

Implementation order:

1. byte embedding,
2. RMSNorm,
3. RoPE,
4. causal self-attention,
5. Transformer block,
6. next-byte softmax head,
7. explicit training loop,
8. checkpoint and metrics logging.

The goal is educational transparency first, then optimization. High-level pretrained-model libraries are not part of the initial implementation.
