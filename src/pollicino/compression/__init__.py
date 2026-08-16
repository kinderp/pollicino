"""Deterministic lossless coding primitives for POLLICINO."""

from .adaptive import AdaptiveNGramCDFProvider, NeuralPriorAdaptiveCDFProvider, adaptive_fingerprint
from .codec import decode_pol, encode_shared, encode_static_histogram, encode_uniform, inspect_pol
from .gating import DeterministicExpertGateCDFProvider, RollingLikelihoodGate, expert_gate_fingerprint
from .models import Order1CountModel, uniform_cdf
from .quantization import frequencies_to_cdf, probabilities_to_frequencies

__all__ = [
    "AdaptiveNGramCDFProvider",
    "NeuralPriorAdaptiveCDFProvider",
    "adaptive_fingerprint",
    "DeterministicExpertGateCDFProvider",
    "RollingLikelihoodGate",
    "expert_gate_fingerprint",
    "decode_pol",
    "encode_shared",
    "encode_static_histogram",
    "encode_uniform",
    "inspect_pol",
    "Order1CountModel",
    "uniform_cdf",
    "frequencies_to_cdf",
    "probabilities_to_frequencies",
]
