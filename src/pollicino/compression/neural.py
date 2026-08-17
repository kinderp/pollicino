from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict

from .models import uniform_cdf
from .quantization import frequencies_to_cdf, probabilities_to_frequencies


def torch_model_fingerprint(model, spec) -> bytes:
    digest = hashlib.sha256()
    digest.update(json.dumps(asdict(spec), sort_keys=True, separators=(",", ":")).encode())
    state = model.state_dict()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(json.dumps(list(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.digest()


class PyTorchCDFProvider:
    """Deterministic byte CDF provider backed by a frozen PyTorch model.

    ``model_evaluations`` counts actual model forward passes rather than wrapper
    calls.  The provider caches by exact context, so several experts sharing this
    provider may request the same prefix without multiplying neural compute.
    ``cache_hits`` is reported separately for experiment diagnostics.
    """

    def __init__(self, model, spec, *, precision_bits: int = 15, device: str = "cpu"):
        import torch

        self.torch = torch
        self.model = model.to(device)
        self.model.eval()
        self.spec = spec
        self.device = device
        self.precision_bits = precision_bits
        self._uniform = uniform_cdf(spec.vocab_size, precision_bits)
        self._cache: dict[bytes, list[int]] = {}
        self.model_evaluations = 0
        self.cache_hits = 0

    def __call__(self, _index: int, prefix: Sequence[int]):
        if not prefix:
            return self._uniform
        context = bytes(prefix[-self.spec.context_length :])
        cached = self._cache.get(context)
        if cached is not None:
            self.cache_hits += 1
            return cached

        indices = self.torch.tensor([list(context)], dtype=self.torch.long, device=self.device)
        with self.torch.no_grad():
            logits = self.model(indices)[0, -1]
            probabilities = self.torch.softmax(logits, dim=-1).detach().cpu().double().tolist()
        cdf = frequencies_to_cdf(probabilities_to_frequencies(probabilities, self.precision_bits))
        self._cache[context] = cdf
        self.model_evaluations += 1
        return cdf
