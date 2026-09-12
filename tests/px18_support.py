from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from typing import Sequence

from pollicino.net.endpoint import RecordKind


REPOSITORY = Path(__file__).parents[1]
LOOPBACK = "127.0.0.1"


@dataclass(frozen=True, slots=True)
class UDPContactResult:
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


def _reserved() -> socket.socket:
    active = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    active.bind((LOOPBACK, 0))
    return active


def _worker_command(
    root: Path,
    local: tuple[str, int],
    peer: tuple[str, int],
    fd: int,
    *,
    role: str,
    kind: RecordKind,
    mtu: int,
    exact: bool,
    max_messages: int,
    timeout: float,
    extra: Sequence[str],
) -> list[str]:
    value = [
        sys.executable, "-m", "pollicino.net.udp_worker",
        "--root", str(root), "--local-host", local[0], "--local-port", str(local[1]),
        "--peer-host", peer[0], "--peer-port", str(peer[1]), "--socket-fd", str(fd),
        "--role", role, "--kind", kind.name, "--mtu", str(mtu),
        "--timeout", str(timeout), "--max-messages", str(max_messages), *extra,
    ]
    if exact:
        value.append("--exact")
    return value


def run_udp_contact(
    source_root: Path,
    receiver_root: Path,
    *,
    kind: RecordKind,
    mtu: int = 128,
    exact: bool = False,
    max_messages: int = 100,
    timeout: float = 0.45,
    initiator_extra: Sequence[str] = (),
    responder_extra: Sequence[str] = (),
    initiator_root: Path | None = None,
    responder_root: Path | None = None,
) -> UDPContactResult:
    a, b = _reserved(), _reserved()
    a_address, b_address = a.getsockname(), b.getsockname()
    active_initiator = source_root if initiator_root is None else initiator_root
    active_responder = receiver_root if responder_root is None else responder_root
    responder = subprocess.Popen(
        _worker_command(
            active_responder, b_address, a_address, b.fileno(), role="responder",
            kind=kind, mtu=mtu, exact=False, max_messages=max_messages,
            timeout=timeout, extra=responder_extra,
        ),
        cwd=REPOSITORY, env=_env(), pass_fds=(b.fileno(),),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    initiator = subprocess.Popen(
        _worker_command(
            active_initiator, a_address, b_address, a.fileno(), role="initiator",
            kind=kind, mtu=mtu, exact=exact, max_messages=max_messages,
            timeout=timeout, extra=initiator_extra,
        ),
        cwd=REPOSITORY, env=_env(), pass_fds=(a.fileno(),),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    a.close(); b.close()
    initiator_stdout, initiator_stderr = initiator.communicate(timeout=12)
    responder_stdout, responder_stderr = responder.communicate(timeout=12)
    assert initiator_stdout == b"" and responder_stdout == b""
    return UDPContactResult(
        initiator.returncode,
        responder.returncode,
        _diag(initiator_stderr),
        _diag(responder_stderr),
    )


def run_udp_reference_contact(
    source_root: Path,
    receiver_root: Path,
    selected: Sequence[bytes],
    *,
    mtu: int = 128,
) -> UDPContactResult:
    extra: list[str] = []
    for key in selected:
        extra.extend(("--selected", key.hex()))
    return run_udp_contact(
        source_root,
        receiver_root,
        kind=RecordKind.REFERENCE,
        mtu=mtu,
        initiator_extra=extra,
        initiator_root=receiver_root,
        responder_root=source_root,
    )


def run_udp_relay_contact(
    source_root: Path,
    receiver_root: Path,
    *,
    kind: RecordKind,
    action: str = "PASS",
    mtu: int = 128,
    exact: bool = False,
    drop_index: int = 1,
) -> UDPContactResult:
    a, b, relay_socket = _reserved(), _reserved(), _reserved()
    a_address, b_address, relay_address = a.getsockname(), b.getsockname(), relay_socket.getsockname()
    relay = subprocess.Popen(
        [
            sys.executable, str(REPOSITORY / "tests" / "px18_udp_relay_worker.py"),
            "--socket-fd", str(relay_socket.fileno()),
            "--a-port", str(a_address[1]), "--b-port", str(b_address[1]),
            "--action", action,
            "--drop-index", str(drop_index),
        ],
        cwd=REPOSITORY, env=_env(), pass_fds=(relay_socket.fileno(),),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    responder = subprocess.Popen(
        _worker_command(
            receiver_root, b_address, relay_address, b.fileno(), role="responder",
            kind=kind, mtu=mtu, exact=False, max_messages=100, timeout=0.45, extra=(),
        ),
        cwd=REPOSITORY, env=_env(), pass_fds=(b.fileno(),),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    initiator = subprocess.Popen(
        _worker_command(
            source_root, a_address, relay_address, a.fileno(), role="initiator",
            kind=kind, mtu=mtu, exact=exact, max_messages=100, timeout=0.45, extra=(),
        ),
        cwd=REPOSITORY, env=_env(), pass_fds=(a.fileno(),),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    a.close(); b.close(); relay_socket.close()
    i_out, i_err = initiator.communicate(timeout=12)
    r_out, r_err = responder.communicate(timeout=12)
    relay_out, relay_err = relay.communicate(timeout=12)
    assert not i_out and not r_out and not relay_out
    return UDPContactResult(
        initiator.returncode, responder.returncode,
        _diag(i_err), _diag(r_err), _diag(relay_err),
    )
