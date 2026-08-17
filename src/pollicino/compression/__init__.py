"""Deterministic lossless coding primitives for POLLICINO."""

from .adaptive import AdaptiveNGramCDFProvider, NeuralPriorAdaptiveCDFProvider, adaptive_fingerprint
from .bit_credit_routing import BitCreditSpecialistRouterCDFProvider, bit_credit_router_fingerprint
from .block_routing import BlockLocalBitCreditRouterCDFProvider, BlockResetCDFProvider, block_local_router_fingerprint
from .classical_experts import RunLengthCDFProvider, run_length_fingerprint
from .codec import decode_pol, encode_shared, encode_static_histogram, encode_uniform, inspect_pol
from .gating import DeterministicExpertGateCDFProvider, RollingLikelihoodGate, expert_gate_fingerprint
from .models import Order1CountModel, uniform_cdf
from .quantization import frequencies_to_cdf, probabilities_to_frequencies
from .routing import CostAwareSpecialistRouterCDFProvider, cost_aware_router_fingerprint
from .sequential_routing import SequentialSpecialistRouterCDFProvider, sequential_router_fingerprint
from .stability_routing import (
    StabilityValueSpecialistRouterCDFProvider,
    stability_value_router_fingerprint,
)

__all__ = [
    "AdaptiveNGramCDFProvider",
    "NeuralPriorAdaptiveCDFProvider",
    "adaptive_fingerprint",
    "BitCreditSpecialistRouterCDFProvider",
    "bit_credit_router_fingerprint",
    "BlockLocalBitCreditRouterCDFProvider",
    "BlockResetCDFProvider",
    "block_local_router_fingerprint",
    "RunLengthCDFProvider",
    "run_length_fingerprint",
    "DeterministicExpertGateCDFProvider",
    "RollingLikelihoodGate",
    "expert_gate_fingerprint",
    "CostAwareSpecialistRouterCDFProvider",
    "cost_aware_router_fingerprint",
    "SequentialSpecialistRouterCDFProvider",
    "sequential_router_fingerprint",
    "StabilityValueSpecialistRouterCDFProvider",
    "stability_value_router_fingerprint",
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
