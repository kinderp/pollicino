from dataclasses import dataclass

import pytest

torch = pytest.importorskip("torch")

from pollicino.compression.codec import decode_pol, encode_shared
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint


@dataclass(frozen=True)
class Spec:
    vocab_size: int = 256
    context_length: int = 8


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.table = torch.nn.Embedding(256, 256)

    def forward(self, indices):
        return self.table(indices)


def test_same_runtime_roundtrip():
    torch.manual_seed(7)
    spec = Spec()
    a = Tiny()
    state = a.state_dict()
    fp = torch_model_fingerprint(a, spec)
    pa = PyTorchCDFProvider(a, spec, precision_bits=12)
    data = b"POLLICINO-POLLICINO"
    blob = encode_shared(data, pa, fp, precision_bits=12)

    b = Tiny()
    b.load_state_dict(state)
    fp2 = torch_model_fingerprint(b, spec)
    pb = PyTorchCDFProvider(b, spec, precision_bits=12)
    assert fp2 == fp
    assert decode_pol(blob, shared_provider=pb, expected_model_fingerprint=fp2) == data


def test_fingerprint_changes():
    torch.manual_seed(1)
    spec = Spec()
    assert torch_model_fingerprint(Tiny(), spec) != torch_model_fingerprint(Tiny(), spec)


def test_model_evaluations_count_cache_misses_not_wrapper_calls():
    torch.manual_seed(11)
    provider = PyTorchCDFProvider(Tiny(), Spec(), precision_bits=12)

    # Empty context is the fixed uniform distribution and needs no model forward.
    provider(0, [])
    assert provider.model_evaluations == 0

    prefix = [65, 66, 67]
    first = provider(len(prefix), prefix)
    second = provider(len(prefix), prefix)
    assert first == second
    assert provider.model_evaluations == 1
    assert provider.cache_hits == 1

    provider(4, [65, 66, 67, 68])
    assert provider.model_evaluations == 2
