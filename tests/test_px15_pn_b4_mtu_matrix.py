from __future__ import annotations

import math

import pytest

from pollicino.net.fragmentation import (
    FRAGMENT_HEADER_BYTES,
    EphemeralFragmentReassembler,
    fragmentation_accounting,
    fragment_message,
)
from test_px15_pn_b4_fragment_codec import MTUS, messages


@pytest.mark.parametrize("mtu", MTUS)
@pytest.mark.parametrize("message_index", range(5))
def test_mtu_size_matrix_roundtrips(mtu: int, message_index: int) -> None:
    encoded = messages()[message_index]
    accounting = fragmentation_accounting(encoded, max_frame_bytes=mtu)
    expected = math.ceil(len(encoded) / (mtu - FRAGMENT_HEADER_BYTES))
    assert accounting.fragment_count == expected
    assert accounting.total_fragment_bytes == len(encoded) + expected * FRAGMENT_HEADER_BYTES
    receiver = EphemeralFragmentReassembler(max_frame_bytes=mtu)
    completed = None
    for frame in fragment_message(encoded, max_frame_bytes=mtu):
        completed = receiver.add(frame.encode()).complete_message or completed
    assert completed == encoded


def test_one_fragment_overhead_is_exact_header_size() -> None:
    encoded = messages()[0]
    accounting = fragmentation_accounting(encoded, max_frame_bytes=4096)
    assert accounting.fragment_count == 1
    assert accounting.fragment_overhead_bytes == FRAGMENT_HEADER_BYTES
