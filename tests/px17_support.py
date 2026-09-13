from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Sequence

from pollicino.net.endpoint import RecordKind


REPOSITORY = Path(__file__).parents[1]


@dataclass(frozen=True, slots=True)
class StreamContactResult:
    initiator_returncode: int
    responder_returncode: int
    initiator: dict[str, object]
    responder: dict[str, object]


def _env() -> dict[str, str]:
    value = dict(os.environ)
    value["PYTHONPATH"] = str(REPOSITORY / "src")
    return value


def _diag(data: bytes) -> dict[str, object]:
    lines = data.decode().splitlines()
    return json.loads(lines[-1]) if lines else {}


def run_stream_contact(
    source_root: Path,
    receiver_root: Path,
    *,
    kind: RecordKind,
    mtu: int = 128,
    exact: bool = False,
    max_messages: int = 100,
    timeout: float = 0.45,
    read_size: int | None = None,
    write_chunk: int | None = None,
    initiator_extra: Sequence[str] = (),
    responder_extra: Sequence[str] = (),
    initiator_root: Path | None = None,
    responder_root: Path | None = None,
) -> StreamContactResult:
    active_initiator = source_root if initiator_root is None else initiator_root
    active_responder = receiver_root if responder_root is None else responder_root
    with tempfile.TemporaryDirectory(prefix="px17-", dir="/tmp") as raw:
        listener_path = Path(raw) / "contact.sock"
        common = [
            "--listener", str(listener_path), "--mtu", str(mtu),
            "--timeout", str(timeout), "--max-messages", str(max_messages),
        ]
        if read_size is not None:
            common.extend(("--read-size", str(read_size)))
        if write_chunk is not None:
            common.extend(("--write-chunk", str(write_chunk)))
        responder = subprocess.Popen(
            [
                sys.executable, "-m", "pollicino.net.unix_stream_worker",
                "--root", str(active_responder), "--role", "responder",
                "--kind", kind.name, *common, *responder_extra,
            ],
            cwd=REPOSITORY,
            env=_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 2
        while not listener_path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert listener_path.exists(), responder.stderr.read().decode() if responder.stderr else ""
        command = [
            sys.executable, "-m", "pollicino.net.unix_stream_worker",
            "--root", str(active_initiator), "--role", "initiator",
            "--kind", kind.name, *common, *initiator_extra,
        ]
        if exact:
            command.append("--exact")
        initiator = subprocess.run(
            command,
            cwd=REPOSITORY,
            env=_env(),
            capture_output=True,
            check=False,
            timeout=12,
        )
        responder_stdout, responder_stderr = responder.communicate(timeout=12)
        assert initiator.stdout == b"" and responder_stdout == b""
        return StreamContactResult(
            initiator.returncode,
            responder.returncode,
            _diag(initiator.stderr),
            _diag(responder_stderr),
        )


def run_stream_reference_contact(
    source_root: Path,
    receiver_root: Path,
    selected: Sequence[bytes],
    *,
    mtu: int = 128,
) -> StreamContactResult:
    extra: list[str] = []
    for key in selected:
        extra.extend(("--selected", key.hex()))
    return run_stream_contact(
        source_root,
        receiver_root,
        kind=RecordKind.REFERENCE,
        mtu=mtu,
        initiator_extra=extra,
        initiator_root=receiver_root,
        responder_root=source_root,
    )
