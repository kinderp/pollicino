from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence

from pollicino.net.endpoint import RecordKind
from pollicino.net.compact_reconciliation import CompactIndependentEndpoint
from pollicino.net.fragmentation import (
    BoundedFragmentStreamReader,
    FRAGMENT_HEADER_BYTES,
    FragmentFrame,
    FragmentationError,
)


REPOSITORY = Path(__file__).parents[1]


def compact_summary() -> bytes:
    from px10_support import memory_endpoint, query

    endpoint = memory_endpoint("compact")
    endpoint.query_results.add_query(query(1))
    return CompactIndependentEndpoint(endpoint.catalog, endpoint.query_results).summary_message(
        RecordKind.QUERY, 10
    )


@dataclass(frozen=True, slots=True)
class FragmentWorkerResult:
    returncode: int
    frame_groups: tuple[tuple[bytes, ...], ...]
    stdout: bytes
    diagnostics: dict[str, object]


@dataclass(frozen=True, slots=True)
class FragmentedContactResult:
    completed: bool
    protocol_messages: int
    logical_message_bytes: int
    fragment_frames: int
    fragment_bytes: int
    fragment_overhead_bytes: int
    durable_commits: int
    process_ids: tuple[int, ...]
    decision: str
    failed_message: int | None


def _environment() -> dict[str, str]:
    value = dict(os.environ)
    value["PYTHONPATH"] = str(REPOSITORY / "src")
    return value


def parse_fragment_stream(data: bytes, *, mtu: int, chunk_size: int = 65536) -> tuple[bytes, ...]:
    reader = BoundedFragmentStreamReader(max_frame_bytes=mtu)
    frames: list[bytes] = []
    for offset in range(0, len(data), chunk_size):
        frames.extend(reader.feed(data[offset : offset + chunk_size]))
    reader.close()
    return tuple(frames)


def group_frames(frames: Sequence[bytes], *, mtu: int) -> tuple[tuple[bytes, ...], ...]:
    groups: list[list[bytes]] = []
    active_id: bytes | None = None
    for encoded in frames:
        frame = FragmentFrame.decode(encoded, max_frame_bytes=mtu)
        if frame.message_id != active_id:
            groups.append([])
            active_id = frame.message_id
        groups[-1].append(encoded)
    return tuple(tuple(group) for group in groups)


def run_fragment_worker(
    root: Path,
    operation: str,
    *,
    mtu: int,
    frame_groups: Sequence[Sequence[bytes]] = (),
    kind: RecordKind | None = None,
    role: str = "GENERIC",
    selected: Sequence[bytes] = (),
    read_size: int = 4096,
    write_chunk_size: int = 65536,
    max_attempts: int = 100,
    crash_after_commit: bool = False,
    crash_after_reassembly: bool = False,
    diagnostic: bool = False,
    timeout: float = 10,
) -> FragmentWorkerResult:
    command = [
        sys.executable, "-m", "pollicino.net.process_worker",
        "--root", str(root), "--operation", operation,
        "--role", role, "--read-size", str(read_size),
        "--write-chunk-size", str(write_chunk_size),
        "--max-attempts", str(max_attempts),
        "--fragment-mtu", str(mtu),
    ]
    if kind is not None:
        command.extend(("--kind", kind.name))
    for key in selected:
        command.extend(("--selected", key.hex()))
    if crash_after_commit:
        command.append("--crash-after-commit")
    if crash_after_reassembly:
        command.append("--crash-after-reassembly")
    if diagnostic:
        command.append("--diagnostic")
    completed = subprocess.run(
        command,
        input=b"".join(frame for group in frame_groups for frame in group),
        cwd=REPOSITORY,
        env=_environment(),
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    lines = completed.stderr.decode("utf-8").splitlines()
    diagnostics = json.loads(lines[-1]) if lines else {}
    frames = parse_fragment_stream(completed.stdout, mtu=mtu, chunk_size=1) if completed.stdout else ()
    return FragmentWorkerResult(
        completed.returncode,
        group_frames(frames, mtu=mtu),
        completed.stdout,
        diagnostics,
    )


def run_fragmented_contact(
    source: Path,
    receiver: Path,
    *,
    kind: RecordKind,
    mtu: int,
    adaptive: bool = True,
    selected: Sequence[bytes] = (),
    max_protocol_messages: int = 100,
    max_fragment_frames: int = 10_000,
    impair_message: int | None = None,
    drop_indexes: Sequence[int] = (),
    duplicate_indexes: Sequence[int] = (),
    reverse: bool = False,
    corrupt_index: int | None = None,
    stop_before_message: int | None = None,
) -> FragmentedContactResult:
    start = run_fragment_worker(
        source,
        "adaptive-start" if adaptive else "exact-start",
        mtu=mtu,
        kind=kind,
        selected=selected,
        max_attempts=max_protocol_messages,
    )
    if start.returncode:
        raise AssertionError(start.diagnostics)
    compact = start.diagnostics.get("decision") == "COMPACT_10"
    queue: deque[tuple[Path, Path, tuple[bytes, ...], str]] = deque(
        (
            receiver,
            source,
            group,
            "RESPONDER" if compact else "GENERIC",
        )
        for group in start.frame_groups
    )
    processes = [int(start.diagnostics["process_id"])]
    messages = logical_bytes = frames = frame_bytes = overhead = commits = 0
    first_compact_response = compact
    while queue:
        if messages >= max_protocol_messages or frames >= max_fragment_frames:
            return FragmentedContactResult(False, messages, logical_bytes, frames, frame_bytes, overhead, commits, tuple(processes), str(start.diagnostics.get("decision")), messages + 1)
        number = messages + 1
        if stop_before_message == number:
            return FragmentedContactResult(False, messages, logical_bytes, frames, frame_bytes, overhead, commits, tuple(processes), str(start.diagnostics.get("decision")), number)
        target, other, group, role = queue.popleft()
        active = list(group)
        if impair_message == number:
            active = [frame for index, frame in enumerate(active) if index not in set(drop_indexes)]
            for index in sorted(duplicate_indexes, reverse=True):
                if 0 <= index < len(active):
                    active.insert(index, active[index])
            if reverse:
                active.reverse()
            if corrupt_index is not None and 0 <= corrupt_index < len(active):
                changed = bytearray(active[corrupt_index]); changed[-1] ^= 1
                active[corrupt_index] = bytes(changed)
        messages += 1
        frames += len(active)
        frame_bytes += sum(map(len, active))
        if not active:
            return FragmentedContactResult(False, messages, logical_bytes, frames, frame_bytes, overhead, commits, tuple(processes), str(start.diagnostics.get("decision")), number)
        overhead += len(active) * FRAGMENT_HEADER_BYTES
        try:
            decoded = [FragmentFrame.decode(frame, max_frame_bytes=mtu) for frame in active]
            unique = {frame.index: frame for frame in decoded}
            if len(unique) == decoded[0].count:
                logical_bytes += decoded[0].total_length
        except FragmentationError:
            # The semantic-blind relay forwards malformed frames. Receiver-side
            # B4 validation, not the harness, owns the failure decision.
            pass
        result = run_fragment_worker(
            target,
            "consume",
            mtu=mtu,
            frame_groups=(tuple(active),),
            role=role,
            selected=selected if target == receiver else (),
            read_size=1 if number % 2 else min(mtu * 2, 4096),
            write_chunk_size=1 if number % 3 == 0 else 65536,
        )
        processes.append(int(result.diagnostics.get("process_id", -1)))
        if result.returncode:
            return FragmentedContactResult(False, messages, logical_bytes, frames, frame_bytes, overhead, commits, tuple(processes), str(start.diagnostics.get("decision")), number)
        commits += int(result.diagnostics.get("durable_commits", 0))
        for group_out in result.frame_groups:
            next_role = "INITIATOR" if first_compact_response and target == receiver else "GENERIC"
            queue.append((other, target, group_out, next_role))
        if first_compact_response and target == receiver:
            first_compact_response = False
    return FragmentedContactResult(True, messages, logical_bytes, frames, frame_bytes, overhead, commits, tuple(processes), str(start.diagnostics.get("decision")), None)


def run_fragmented_reference_contact(
    source: Path,
    receiver: Path,
    selected: Sequence[bytes],
    *,
    mtu: int,
) -> FragmentedContactResult:
    start = run_fragment_worker(receiver, "reference-start", mtu=mtu)
    queue: deque[tuple[Path, Path, tuple[bytes, ...]]] = deque(
        (source, receiver, group) for group in start.frame_groups
    )
    processes = [int(start.diagnostics["process_id"])]
    messages = logical = frames = wire = overhead = commits = 0
    while queue:
        target, other, group = queue.popleft()
        messages += 1; frames += len(group); wire += sum(map(len, group))
        decoded = [FragmentFrame.decode(frame, max_frame_bytes=mtu) for frame in group]
        logical += decoded[0].total_length
        overhead += len(group) * 52
        result = run_fragment_worker(
            target, "consume", mtu=mtu, frame_groups=(group,),
            selected=selected if target == receiver else (), read_size=1,
        )
        processes.append(int(result.diagnostics.get("process_id", -1)))
        if result.returncode:
            return FragmentedContactResult(False, messages, logical, frames, wire, overhead, commits, tuple(processes), "EXPLICIT_REFERENCE", messages)
        commits += int(result.diagnostics.get("durable_commits", 0))
        queue.extend((other, target, value) for value in result.frame_groups)
    return FragmentedContactResult(True, messages, logical, frames, wire, overhead, commits, tuple(processes), "EXPLICIT_REFERENCE", None)
