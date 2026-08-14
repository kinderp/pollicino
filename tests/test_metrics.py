import math

from pollicino.common.metrics import mean_bits_per_symbol, nats_to_bits


def test_nats_to_bits_for_probability_half() -> None:
    assert math.isclose(nats_to_bits(-math.log(0.5)), 1.0)


def test_mean_bits_per_symbol_uniform_bytes() -> None:
    # p = 1/256 -> exactly 8 ideal bits per byte
    nll = -math.log(1 / 256)
    assert math.isclose(mean_bits_per_symbol([nll, nll]), 8.0)
