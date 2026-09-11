from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Sequence

from pollicino.net.compact_reconciliation import (
    B2C_MAGIC,
    SketchSummaryMessage,
    decode_compact_message,
)
from pollicino.net.endpoint import RecordKind
from pollicino.net.process_io import BoundedMessageStreamReader


REPOSITORY = Path(__file__).parents[1]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    returncode: int
    messages: tuple[bytes, ...]
    stdout: bytes
    diagnostics: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProcessContactResult:
    completed: bool
    protocol_messages: int
    protocol_bytes: int
    durable_commits: int
    process_ids: tuple[int, ...]
    decisions: tuple[str, ...]
    stopped_at: int | None


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY / "src")
    return environment


def split_bytes(data: bytes, sizes: Iterable[int]) -> tuple[bytes, ...]:
    pattern = tuple(sizes)
    if not pattern or any(size < 1 for size in pattern):
        raise ValueError("segmentation sizes must be positive")
    blocks: list[bytes] = []
    offset = 0
    index = 0
    while offset < len(data):
        size = pattern[index % len(pattern)]
        blocks.append(data[offset : offset + size])
        offset += size
        index += 1
    return tuple(blocks)


def parse_stream(data: bytes, sizes: Sequence[int] = (65536,)) -> tuple[bytes, ...]:
    reader = BoundedMessageStreamReader()
    messages: list[bytes] = []
    for block in split_bytes(data, sizes):
        messages.extend(reader.feed(block))
    reader.close()
    return tuple(messages)


def run_worker(
    root: Path,
    operation: str,
    *,
    messages: Sequence[bytes] = (),
    kind: RecordKind | None = None,
    role: str = "GENERIC",
    selected: Sequence[bytes] = (),
    read_size: int = 4096,
    write_chunk_size: int = 65536,
    max_attempts: int = 100,
    diagnostic: bool = False,
    crash_after_commit: bool = False,
    timeout: float = 10.0,
    output_segments: Sequence[int] = (65536,),
) -> WorkerResult:
    command = [
        sys.executable,
        "-m",
        "pollicino.net.process_worker",
        "--root",
        str(root),
        "--operation",
        operation,
        "--role",
        role,
        "--read-size",
        str(read_size),
        "--write-chunk-size",
        str(write_chunk_size),
        "--max-attempts",
        str(max_attempts),
    ]
    if kind is not None:
        command.extend(("--kind", kind.name))
    for key in selected:
        command.extend(("--selected", key.hex()))
    if diagnostic:
        command.append("--diagnostic")
    if crash_after_commit:
        command.append("--crash-after-commit")
    completed = subprocess.run(
        command,
        input=b"".join(messages),
        cwd=REPOSITORY,
        env=_environment(),
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    lines = completed.stderr.decode("utf-8").splitlines()
    diagnostics = json.loads(lines[-1]) if lines else {}
    decoded = parse_stream(completed.stdout, output_segments) if completed.stdout else ()
    return WorkerResult(
        completed.returncode, decoded, completed.stdout, diagnostics
    )


def run_directional_contact(
    source: Path,
    receiver: Path,
    *,
    kind: RecordKind,
    adaptive: bool = True,
    selected: Sequence[bytes] = (),
    max_attempts: int = 100,
    stop_before_attempt: int | None = None,
    drop_attempts: Sequence[int] = (),
    corrupt_attempts: Sequence[int] = (),
    output_segments: Sequence[int] = (7,),
) -> ProcessContactResult:
    start = run_worker(
        source,
        "adaptive-start" if adaptive else "exact-start",
        kind=kind,
        selected=selected,
        max_attempts=max_attempts,
        output_segments=output_segments,
    )
    if start.returncode:
        raise AssertionError(start.diagnostics)
    queue: deque[tuple[Path, Path, bytes]] = deque(
        (receiver, source, message) for message in start.messages
    )
    processes = [int(start.diagnostics["process_id"])]
    decisions = [str(start.diagnostics.get("decision", "EXACT"))]
    attempts = 0
    octets = 0
    commits = 0
    drop_set = set(drop_attempts)
    corrupt_set = set(corrupt_attempts)
    while queue:
        attempts += 1
        if attempts > max_attempts:
            return ProcessContactResult(
                False, attempts - 1, octets, commits, tuple(processes), tuple(decisions), attempts
            )
        if stop_before_attempt == attempts:
            return ProcessContactResult(
                False, attempts - 1, octets, commits, tuple(processes), tuple(decisions), attempts
            )
        target, other, encoded = queue.popleft()
        role = "GENERIC"
        if encoded[:4] == B2C_MAGIC:
            decoded = decode_compact_message(encoded)
            if isinstance(decoded, SketchSummaryMessage):
                role = "RESPONDER" if target == receiver else "INITIATOR"
        if attempts in drop_set:
            continue
        if attempts in corrupt_set:
            mutable = bytearray(encoded)
            mutable[-1] ^= 1
            encoded = bytes(mutable)
        active_selected = selected if target == receiver else ()
        result = run_worker(
            target,
            "consume",
            messages=(encoded,),
            role=role,
            selected=active_selected,
            read_size=1 if attempts % 3 == 0 else 17,
            write_chunk_size=1 if attempts % 4 == 0 else 65536,
            output_segments=output_segments,
        )
        processes.append(int(result.diagnostics.get("process_id", -1)))
        octets += len(encoded)
        if result.returncode:
            return ProcessContactResult(
                False, attempts, octets, commits, tuple(processes), tuple(decisions), attempts
            )
        commits += int(result.diagnostics.get("durable_commits", 0))
        queue.extend((other, target, message) for message in result.messages)
    return ProcessContactResult(
        True, attempts, octets, commits, tuple(processes), tuple(decisions), None
    )


def run_reference_contact(
    source: Path,
    receiver: Path,
    selected: Sequence[bytes],
    *,
    max_attempts: int = 100,
) -> ProcessContactResult:
    start = run_worker(receiver, "reference-start")
    if start.returncode:
        raise AssertionError(start.diagnostics)
    queue: deque[tuple[Path, Path, bytes]] = deque(
        (source, receiver, message) for message in start.messages
    )
    processes = [int(start.diagnostics["process_id"])]
    attempts = 0
    octets = 0
    commits = 0
    while queue:
        attempts += 1
        if attempts > max_attempts:
            return ProcessContactResult(False, attempts - 1, octets, commits, tuple(processes), ("EXPLICIT_REFERENCE",), attempts)
        target, other, encoded = queue.popleft()
        result = run_worker(
            target,
            "consume",
            messages=(encoded,),
            selected=selected if target == receiver else (),
            read_size=1 if attempts % 2 else 29,
        )
        processes.append(int(result.diagnostics.get("process_id", -1)))
        octets += len(encoded)
        if result.returncode:
            return ProcessContactResult(False, attempts, octets, commits, tuple(processes), ("EXPLICIT_REFERENCE",), attempts)
        commits += int(result.diagnostics.get("durable_commits", 0))
        queue.extend((other, target, message) for message in result.messages)
    return ProcessContactResult(True, attempts, octets, commits, tuple(processes), ("EXPLICIT_REFERENCE",), None)
