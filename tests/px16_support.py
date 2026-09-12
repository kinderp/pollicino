from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from pollicino.net.endpoint import RecordKind


REPOSITORY = Path(__file__).parents[1]


@dataclass(frozen=True, slots=True)
class UnixContactResult:
    initiator_returncode: int
    responder_returncode: int
    initiator: dict[str, object]
    responder: dict[str, object]
    relay: dict[str, object] | None = None


def _env() -> dict[str, str]:
    value = dict(os.environ)
    value["PYTHONPATH"] = str(REPOSITORY / "src")
    return value


def _diag(data: bytes) -> dict[str, object]:
    lines = data.decode().splitlines()
    return json.loads(lines[-1]) if lines else {}


def run_unix_contact(
    source_root: Path,
    receiver_root: Path,
    *,
    kind: RecordKind,
    mtu: int = 128,
    exact: bool = False,
    max_messages: int = 100,
    receiver_extra: tuple[str, ...] = (),
) -> UnixContactResult:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        sockets = Path(raw)
        source_path, receiver_path = sockets / "a.sock", sockets / "b.sock"
        common = ["--mtu", str(mtu), "--timeout", "0.35", "--max-messages", str(max_messages)]
        responder = subprocess.Popen(
            [sys.executable, "-m", "pollicino.net.unix_datagram_worker",
             "--root", str(receiver_root), "--local", str(receiver_path),
             "--peer", str(source_path), "--role", "responder", "--kind", kind.name,
             *common, *receiver_extra],
            cwd=REPOSITORY, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 2
        while not receiver_path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert receiver_path.exists()
        initiator_cmd = [
            sys.executable, "-m", "pollicino.net.unix_datagram_worker",
            "--root", str(source_root), "--local", str(source_path),
            "--peer", str(receiver_path), "--role", "initiator", "--kind", kind.name,
            *common,
        ]
        if exact:
            initiator_cmd.append("--exact")
        initiator = subprocess.run(
            initiator_cmd, cwd=REPOSITORY, env=_env(), capture_output=True,
            check=False, timeout=10,
        )
        responder_stdout, responder_stderr = responder.communicate(timeout=10)
        assert initiator.stdout == b"" and responder_stdout == b""
        return UnixContactResult(
            initiator.returncode, responder.returncode,
            _diag(initiator.stderr), _diag(responder_stderr),
        )


def run_relay_contact(
    source_root: Path,
    receiver_root: Path,
    *,
    kind: RecordKind,
    mtu: int = 128,
    actions: tuple[str, ...] = (),
    exact: bool = False,
) -> UnixContactResult:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        sockets = Path(raw)
        a_path, b_path, relay_path = sockets / "a.sock", sockets / "b.sock", sockets / "r.sock"
        relay = subprocess.Popen(
            [sys.executable, str(REPOSITORY / "tests" / "px16_relay_worker.py"),
             "--local", str(relay_path), "--a", str(a_path), "--b", str(b_path),
             "--actions", ",".join(actions)],
            cwd=REPOSITORY, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 2
        while not relay_path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert relay_path.exists()
        responder = subprocess.Popen(
            [sys.executable, "-m", "pollicino.net.unix_datagram_worker",
             "--root", str(receiver_root), "--local", str(b_path), "--peer", str(relay_path),
             "--role", "responder", "--kind", kind.name, "--mtu", str(mtu), "--timeout", "0.45"],
            cwd=REPOSITORY, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 2
        while not b_path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert b_path.exists()
        command = [sys.executable, "-m", "pollicino.net.unix_datagram_worker",
                   "--root", str(source_root), "--local", str(a_path), "--peer", str(relay_path),
                   "--role", "initiator", "--kind", kind.name, "--mtu", str(mtu), "--timeout", "0.45"]
        if exact: command.append("--exact")
        initiator = subprocess.run(command, cwd=REPOSITORY, env=_env(), capture_output=True, timeout=10)
        r_out, r_err = responder.communicate(timeout=10)
        relay_out, relay_err = relay.communicate(timeout=10)
        assert not initiator.stdout and not r_out and not relay_out
        return UnixContactResult(initiator.returncode, responder.returncode,
                                 _diag(initiator.stderr), _diag(r_err), _diag(relay_err))
