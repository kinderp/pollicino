import math

from pollicino.baselines.uniform import evaluate_bytes


def test_uniform_baseline_is_eight_bits_per_byte_and_lossless() -> None:
    data = bytes(range(256)) * 4
    result = evaluate_bytes(data)
    assert math.isclose(result.theoretical_bits_per_byte, 8.0)
    assert result.input_bytes == len(data)
    assert result.sha256_original == result.sha256_decoded
    assert result.round_trip_ok


def test_uniform_baseline_handles_empty_file() -> None:
    result = evaluate_bytes(b"")
    assert math.isclose(result.theoretical_bits_per_byte, 8.0)
    assert result.input_bytes == 0
    assert result.round_trip_ok
