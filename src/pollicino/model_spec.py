from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ModelSpec:
    """Framework-neutral specification for the reference byte Transformer."""
    vocab_size: int = 256
    context_length: int = 32
    d_model: int = 32
    n_heads: int = 4
    n_layers: int = 2
    d_ff: int = 64
    layer_norm_eps: float = 1e-5
    def __post_init__(self) -> None:
        if self.vocab_size <= 1: raise ValueError("vocab_size must be > 1")
        if self.context_length <= 0: raise ValueError("context_length must be positive")
        if self.d_model <= 0 or self.n_heads <= 0 or self.n_layers <= 0 or self.d_ff <= 0: raise ValueError("model dimensions must be positive")
        if self.d_model % self.n_heads != 0: raise ValueError("d_model must be divisible by n_heads")
    @property
    def head_dim(self) -> int: return self.d_model // self.n_heads

def expected_parameter_count(spec: ModelSpec) -> int:
    embeddings=spec.vocab_size*spec.d_model + spec.context_length*spec.d_model
    qkv=spec.d_model*(3*spec.d_model)+3*spec.d_model
    attention_projection=spec.d_model*spec.d_model+spec.d_model
    two_layer_norms=4*spec.d_model
    feed_forward=(spec.d_model*spec.d_ff+spec.d_ff)+(spec.d_ff*spec.d_model+spec.d_model)
    block=qkv+attention_projection+two_layer_norms+feed_forward
    final_norm=2*spec.d_model
    lm_head=spec.d_model*spec.vocab_size+spec.vocab_size
    return embeddings + spec.n_layers*block + final_norm + lm_head
