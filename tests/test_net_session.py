import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.session import ExactSyncSessionState, sync_missing_chunks_step


def clean_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=1,
    )


def unique_chunks(count: int, chunk_size: int = 64) -> bytes:
    pieces = []
    for index in range(count):
        seed = hashlib.sha256(f"session-chunk-{index}".encode()).digest()
        pieces.append((seed * ((chunk_size + 31) // 32))[:chunk_size])
    return b"".join(pieces)


def test_resumable_session_transfers_only_new_chunks() -> None:
    data = unique_chunks(5)
    sender = PollicinoStore()
    receiver = PollicinoStore()

    reconstructed, state1, first = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=1000,
        max_chunks=2,
        manifest_on_scarce=True,
    )

    assert reconstructed is None
    assert first.transferred_chunk_indices == (0, 1)
    assert first.cached_chunk_count_before == 0
    assert first.missing_chunk_count_before == 5
    assert first.remaining_chunk_count == 3
    assert first.manifest_wire_bytes > 0
    assert len(receiver) == 2
    assert state1.manifest_delivered
    assert not state1.completed

    reconstructed, state2, second = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        state=state1,
        max_chunks=2,
        manifest_on_scarce=True,
    )

    assert reconstructed is None
    assert second.transferred_chunk_indices == (2, 3)
    assert second.cached_chunk_count_before == 2
    assert second.missing_chunk_count_before == 3
    assert second.remaining_chunk_count == 1
    assert second.manifest_wire_bytes == 0
    assert len(receiver) == 4

    reconstructed, state3, third = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        state=state2,
        max_chunks=2,
        manifest_on_scarce=True,
    )

    assert reconstructed == data
    assert third.transferred_chunk_indices == (4,)
    assert third.cached_chunk_count_before == 4
    assert third.remaining_chunk_count == 0
    assert third.complete and third.exact
    assert state3.completed
    assert len(receiver) == 5
    assert state3.cumulative_wire_bytes == (
        first.step_wire_bytes + second.step_wire_bytes + third.step_wire_bytes
    )
    assert state3.cumulative_retransmissions == (
        first.retransmissions + second.retransmissions + third.retransmissions
    )


def test_session_state_round_trip_can_resume() -> None:
    data = unique_chunks(3)
    sender = PollicinoStore()
    receiver = PollicinoStore()

    _, state, first = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=77,
        max_chunks=1,
        manifest_on_scarce=False,
    )
    restored = ExactSyncSessionState.from_dict(state.to_dict())

    assert restored == state
    assert first.manifest_wire_bytes == 0

    reconstructed, final_state, second = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        state=restored,
        max_chunks=10,
        manifest_on_scarce=False,
    )
    assert reconstructed == data
    assert final_state.completed
    assert second.cached_chunk_count_before == 1
    assert second.transferred_chunk_indices == (1, 2)


def test_resume_rejects_different_object_or_changed_manifest_policy() -> None:
    data = unique_chunks(2)
    sender = PollicinoStore()
    receiver = PollicinoStore()
    _, state, _ = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=9,
        max_chunks=1,
        manifest_on_scarce=True,
    )

    with pytest.raises(ValueError, match="different chunk manifest"):
        sync_missing_chunks_step(
            data + b"different",
            chunk_size=64,
            sender_store=sender,
            receiver_store=receiver,
            profile=clean_profile(),
            state=state,
            max_chunks=1,
            manifest_on_scarce=True,
        )

    with pytest.raises(ValueError, match="cannot change"):
        sync_missing_chunks_step(
            data,
            chunk_size=64,
            sender_store=sender,
            receiver_store=receiver,
            profile=clean_profile(),
            state=state,
            max_chunks=1,
            manifest_on_scarce=False,
        )


def test_fully_cached_pre_resolved_session_needs_no_chunk_transfer() -> None:
    data = unique_chunks(4)
    sender = PollicinoStore()
    receiver = PollicinoStore()
    for offset in range(0, len(data), 64):
        receiver.put(data[offset : offset + 64])

    reconstructed, state, report = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=500,
        max_chunks=2,
        manifest_on_scarce=False,
    )

    assert reconstructed == data
    assert state.completed
    assert report.cached_chunk_count_before == 4
    assert report.missing_chunk_count_before == 0
    assert report.transferred_chunk_indices == ()
    assert report.transferred_source_bytes == 0
    assert report.manifest_wire_bytes == 0
    assert report.availability_wire_bytes > 0
    assert report.chunk_wire_bytes == 0


def test_completed_session_resume_is_idempotent_and_zero_wire() -> None:
    data = unique_chunks(1)
    sender = PollicinoStore()
    receiver = PollicinoStore()
    reconstructed, state, _ = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=1,
        max_chunks=1,
        manifest_on_scarce=False,
    )
    assert reconstructed == data and state.completed

    reconstructed_again, unchanged, report = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        state=state,
        max_chunks=1,
        manifest_on_scarce=False,
    )

    assert reconstructed_again == data
    assert unchanged == state
    assert report.step_wire_bytes == 0
    assert report.complete and report.exact
