from dataclasses import replace
import hashlib
import json

import pytest

import pollicino.net.persistence as persistence
from pollicino.net.persistence import (
    DirectoryPollicinoStore,
    load_exact_session_checkpoint,
    save_exact_session_checkpoint,
)
from pollicino.net.session import ExactSyncSessionState, sync_missing_chunks_step
from pollicino.net import ScarceLinkProfile


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
        seed = hashlib.sha256(f"persistent-session-chunk-{index}".encode()).digest()
        pieces.append((seed * ((chunk_size + 31) // 32))[:chunk_size])
    return b"".join(pieces)


def test_directory_store_survives_reopen_and_repairs_corruption(tmp_path) -> None:
    root = tmp_path / "store"
    first = DirectoryPollicinoStore(root)
    content = b"durable-pollicino-chunk" * 5
    digest = first.put(content)

    assert first.has(digest)
    assert first.get(digest) == content
    assert len(first) == 1

    reopened = DirectoryPollicinoStore(root)
    assert reopened.has(digest)
    assert reopened.get(digest) == content
    assert len(reopened) == 1

    chunk_path = reopened.path_for_digest(digest)
    chunk_path.write_bytes(b"corrupt")
    assert not reopened.has(digest)
    assert len(reopened) == 0
    with pytest.raises(ValueError, match="SHA-256"):
        reopened.get(digest)

    repaired = reopened.put(content)
    assert repaired == digest
    assert reopened.has(digest)
    assert reopened.get(digest) == content
    assert len(reopened) == 1


def test_checkpoint_round_trip_and_checksum_tamper_detection(tmp_path) -> None:
    checkpoint = tmp_path / "session.json"
    state = ExactSyncSessionState(
        manifest_fingerprint=bytes(range(32)),
        next_transfer_id=123,
        manifest_on_scarce=True,
        manifest_delivered=True,
        step_count=2,
        cumulative_manifest_wire_bytes=100,
        cumulative_availability_wire_bytes=50,
        cumulative_chunk_wire_bytes=300,
        cumulative_retransmissions=1,
        cumulative_primary_data_wire_bytes=350,
        cumulative_primary_ack_wire_bytes=50,
        cumulative_retransmission_data_wire_bytes=40,
        cumulative_retransmission_ack_wire_bytes=10,
        wire_accounting="model-exact",
    )

    save_exact_session_checkpoint(checkpoint, state)
    assert load_exact_session_checkpoint(checkpoint) == state

    envelope = json.loads(checkpoint.read_text(encoding="utf-8"))
    envelope["state"]["step_count"] = 999
    checkpoint.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_exact_session_checkpoint(checkpoint)


def test_failed_atomic_checkpoint_replace_preserves_previous_state(tmp_path, monkeypatch) -> None:
    checkpoint = tmp_path / "session.json"
    first = ExactSyncSessionState(
        manifest_fingerprint=b"A" * 32,
        next_transfer_id=10,
        manifest_on_scarce=False,
        manifest_delivered=True,
        step_count=1,
    )
    second = replace(first, next_transfer_id=20, step_count=2)
    save_exact_session_checkpoint(checkpoint, first)

    def fail_replace(_source, _destination):
        raise OSError("simulated crash before atomic replace")

    monkeypatch.setattr(persistence.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated crash"):
        save_exact_session_checkpoint(checkpoint, second)

    assert load_exact_session_checkpoint(checkpoint) == first
    assert list(checkpoint.parent.glob(f".{checkpoint.name}.*.tmp")) == []


def test_process_restart_resumes_without_retransmitting_verified_chunks(tmp_path) -> None:
    data = unique_chunks(4)
    sender_root = tmp_path / "sender"
    receiver_root = tmp_path / "receiver"
    checkpoint = tmp_path / "exact-session.json"

    sender_before_restart = DirectoryPollicinoStore(sender_root)
    receiver_before_restart = DirectoryPollicinoStore(receiver_root)
    reconstructed, state_before_restart, first = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender_before_restart,
        receiver_store=receiver_before_restart,
        profile=clean_profile(),
        transfer_id_base=1200,
        max_chunks=2,
        manifest_on_scarce=True,
    )

    assert reconstructed is None
    assert first.transferred_chunk_indices == (0, 1)
    assert first.remaining_chunk_count == 2
    assert len(sender_before_restart) == 4
    assert len(receiver_before_restart) == 2
    save_exact_session_checkpoint(checkpoint, state_before_restart)

    # Simulate a fresh process: reconstruct no Python object from memory.
    sender_after_restart = DirectoryPollicinoStore(sender_root)
    receiver_after_restart = DirectoryPollicinoStore(receiver_root)
    restored = load_exact_session_checkpoint(checkpoint)

    assert len(sender_after_restart) == 4
    assert len(receiver_after_restart) == 2
    assert restored == state_before_restart

    reconstructed, final_state, second = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=sender_after_restart,
        receiver_store=receiver_after_restart,
        profile=clean_profile(),
        state=restored,
        max_chunks=10,
        manifest_on_scarce=True,
    )

    assert reconstructed == data
    assert final_state.completed
    assert second.cached_chunk_count_before == 2
    assert second.missing_chunk_count_before == 2
    assert second.transferred_chunk_indices == (2, 3)
    assert second.manifest_wire_bytes == 0
    assert len(receiver_after_restart) == 4
    assert final_state.cumulative_manifest_wire_bytes == state_before_restart.cumulative_manifest_wire_bytes

    save_exact_session_checkpoint(checkpoint, final_state)
    final_restored = load_exact_session_checkpoint(checkpoint)
    reconstructed_again, unchanged, idempotent = sync_missing_chunks_step(
        data,
        chunk_size=64,
        sender_store=DirectoryPollicinoStore(sender_root),
        receiver_store=DirectoryPollicinoStore(receiver_root),
        profile=clean_profile(),
        state=final_restored,
        max_chunks=10,
        manifest_on_scarce=True,
    )
    assert reconstructed_again == data
    assert unchanged == final_state
    assert idempotent.step_wire_bytes == 0
