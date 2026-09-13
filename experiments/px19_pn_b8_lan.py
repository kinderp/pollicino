from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

from pollicino.net.catalog import BoundedReference
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, ResultRecord


REPOSITORY = Path(__file__).resolve().parents[1]
OVERLAY_PREFIXES = ("lo", "utun", "tun", "tap", "wg", "tailscale", "zt")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ipv4(value: str) -> str:
    parsed = ipaddress.IPv4Address(value)
    if parsed.is_loopback or parsed.is_unspecified or parsed.is_multicast or parsed.is_reserved:
        raise ValueError("PX19 requires an explicit non-loopback unicast IPv4 address")
    return str(parsed)


def _git_state() -> tuple[str, bool]:
    sha = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPOSITORY,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"), cwd=REPOSITORY,
        check=True, capture_output=True, text=True,
    ).stdout
    return sha, not bool(status)


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _run(command: tuple[str, ...]) -> str:
    return subprocess.run(
        command, check=True, capture_output=True, text=True,
    ).stdout


def _route(peer: str) -> tuple[str, str | None, int | None, str]:
    system = platform.system()
    if system == "Darwin":
        raw = _run(("/sbin/route", "-n", "get", peer))
        match = re.search(r"^\s*interface:\s*(\S+)", raw, re.MULTILINE)
        interface = match.group(1) if match else None
        mtu_match = re.search(r"^\s*mtu\s+(\d+)", raw, re.MULTILINE)
        mtu = int(mtu_match.group(1)) if mtu_match else None
        if interface and mtu is None:
            detail = _run(("/sbin/ifconfig", interface))
            mtu_match = re.search(r"\bmtu\s+(\d+)", detail)
            mtu = int(mtu_match.group(1)) if mtu_match else None
        return "route -n get", interface, mtu, raw
    if system == "Linux":
        raw = _run(("ip", "-4", "route", "get", peer))
        match = re.search(r"\bdev\s+(\S+)", raw)
        interface = match.group(1) if match else None
        mtu = None
        if interface:
            mtu_path = Path("/sys/class/net") / interface / "mtu"
            if mtu_path.exists():
                mtu = int(mtu_path.read_text(encoding="utf-8").strip())
        return "ip -4 route get", interface, mtu, raw
    try:
        raw = _run(("route", "print", peer))
    except (OSError, subprocess.CalledProcessError):
        raw = "UNAVAILABLE"
    return "operator-declared with route diagnostic", None, None, raw


def environment(args: argparse.Namespace) -> int:
    local = _ipv4(args.local_ip)
    peer = _ipv4(args.peer_ip)
    method, detected_interface, detected_mtu, raw = _route(peer)
    interface = args.interface or detected_interface
    mtu = args.interface_mtu or detected_mtu
    if not args.physical_host_attestation:
        raise ValueError("--physical-host-attestation is required")
    if not interface or not mtu:
        raise ValueError("interface and MTU must be detected or explicitly supplied")
    lowered = interface.lower()
    overlay = lowered.startswith(OVERLAY_PREFIXES)
    if overlay:
        raise ValueError("loopback/overlay interface is not admissible for PX19")
    sha, clean = _git_state()
    value: dict[str, object] = {
        "role": args.role,
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "commit_sha": sha,
        "worktree_clean": clean,
        "local_ipv4": local,
        "peer_ipv4": peer,
        "interface": interface,
        "interface_mtu": mtu,
        "interface_medium": args.interface_medium,
        "route_method": method,
        "route_diagnostic": raw,
        "loopback_interface_used": False,
        "overlay_or_vpn_used": False,
        "physical_host_attestation": True,
        "recorded_at": _utc_now(),
    }
    _write(args.output, value)
    print(json.dumps(value, sort_keys=True))
    return 0


def _open_root(root: Path) -> tuple[PersistentBoundedReferenceCatalog, PersistentQueryResultStore]:
    return (
        PersistentBoundedReferenceCatalog(root / "catalog"),
        PersistentQueryResultStore(root / "query-result"),
    )


def prepare(args: argparse.Namespace) -> int:
    if any(type(value) is not int or not 0 <= value <= 10_000 for value in (
        args.queries, args.results, args.references,
    )):
        raise ValueError("record counts must be between zero and 10,000")
    if type(args.payload_bytes) is not int or not 0 <= args.payload_bytes <= 4092:
        raise ValueError("payload bytes must be between zero and 4,092")
    if args.root.exists():
        raise FileExistsError("refusing to overwrite an existing durable root")
    args.root.mkdir(parents=True)
    catalog, query_results = _open_root(args.root)
    try:
        payload = b"Q" * args.payload_bytes
        query_results.add_queries(
            QueryRecord(index.to_bytes(4, "big"), payload + index.to_bytes(4, "big"))
            for index in range(args.queries)
        )
        query_results.add_results(
            ResultRecord(
                index.to_bytes(4, "big"), index.to_bytes(4, "big"),
                (b"px19-key-" + index.to_bytes(4, "big"),),
            )
            for index in range(args.results)
        )
        catalog.add_many(
            BoundedReference(
                b"px19-key-" + index.to_bytes(4, "big"),
                b"R" * args.payload_bytes + index.to_bytes(4, "big"),
            )
            for index in range(args.references)
        )
        value = _state(args.root, catalog, query_results)
    finally:
        catalog.close(); query_results.close()
    print(json.dumps(value, sort_keys=True))
    return 0


def _state(
    root: Path,
    catalog: PersistentBoundedReferenceCatalog,
    query_results: PersistentQueryResultStore,
) -> dict[str, object]:
    return {
        "root": str(root),
        "catalog_records": len(catalog),
        "query_records": query_results.query_count,
        "result_records": query_results.result_count,
        "catalog_state_digest": catalog.state_digest.hex(),
        "query_result_state_digest": query_results.state_digest.hex(),
    }


def inspect_root(args: argparse.Namespace) -> int:
    catalog, query_results = _open_root(args.root)
    try:
        value = _state(args.root, catalog, query_results)
    finally:
        catalog.close(); query_results.close()
    if args.output:
        _write(args.output, value)
    print(json.dumps(value, sort_keys=True))
    return 0


def verify_pair(args: argparse.Namespace) -> int:
    host_a = json.loads(args.host_a.read_text(encoding="utf-8"))
    host_b = json.loads(args.host_b.read_text(encoding="utf-8"))
    errors: list[str] = []
    if host_a.get("role") != "A" or host_b.get("role") != "B":
        errors.append("roles must be A and B")
    if host_a.get("local_ipv4") == host_b.get("local_ipv4"):
        errors.append("physical hosts must have distinct LAN IPv4 addresses")
    if host_a.get("peer_ipv4") != host_b.get("local_ipv4") or host_b.get("peer_ipv4") != host_a.get("local_ipv4"):
        errors.append("peer endpoints do not cross-reference")
    shas = {host_a.get("commit_sha"), host_b.get("commit_sha")}
    if len(shas) != 1 or args.expected_sha not in shas:
        errors.append("host implementation SHAs differ from expected SHA")
    if not host_a.get("worktree_clean") or not host_b.get("worktree_clean"):
        errors.append("both scientific worktrees must be clean")
    if not host_a.get("physical_host_attestation") or not host_b.get("physical_host_attestation"):
        errors.append("physical host attestation missing")
    if host_a.get("loopback_interface_used") or host_b.get("loopback_interface_used"):
        errors.append("loopback interface is inadmissible")
    if host_a.get("overlay_or_vpn_used") or host_b.get("overlay_or_vpn_used"):
        errors.append("overlay/VPN interface is inadmissible")
    value: dict[str, object] = {
        "verified": not errors,
        "errors": errors,
        "host_a_sha": host_a.get("commit_sha"),
        "host_b_sha": host_b.get("commit_sha"),
        "same_implementation_sha": len(shas) == 1,
        "two_distinct_lan_addresses": host_a.get("local_ipv4") != host_b.get("local_ipv4"),
        "loopback_interface_used": False if not errors else None,
        "verified_at": _utc_now(),
    }
    _write(args.output, value)
    print(json.dumps(value, sort_keys=True))
    return 0 if not errors else 2


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="px19-pn-b8-lan")
    commands = root.add_subparsers(dest="command", required=True)

    environment_parser = commands.add_parser("environment")
    environment_parser.add_argument("--role", choices=("A", "B"), required=True)
    environment_parser.add_argument("--local-ip", required=True)
    environment_parser.add_argument("--peer-ip", required=True)
    environment_parser.add_argument("--interface")
    environment_parser.add_argument("--interface-mtu", type=int)
    environment_parser.add_argument("--interface-medium", choices=("Ethernet", "Wi-Fi", "unknown"), default="unknown")
    environment_parser.add_argument("--physical-host-attestation", action="store_true")
    environment_parser.add_argument("--output", type=Path, required=True)
    environment_parser.set_defaults(handler=environment)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--root", type=Path, required=True)
    prepare_parser.add_argument("--queries", type=int, default=0)
    prepare_parser.add_argument("--results", type=int, default=0)
    prepare_parser.add_argument("--references", type=int, default=0)
    prepare_parser.add_argument("--payload-bytes", type=int, default=16)
    prepare_parser.set_defaults(handler=prepare)

    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("--root", type=Path, required=True)
    inspect_parser.add_argument("--output", type=Path)
    inspect_parser.set_defaults(handler=inspect_root)

    verify_parser = commands.add_parser("verify-pair")
    verify_parser.add_argument("--host-a", type=Path, required=True)
    verify_parser.add_argument("--host-b", type=Path, required=True)
    verify_parser.add_argument("--expected-sha", required=True)
    verify_parser.add_argument("--output", type=Path, required=True)
    verify_parser.set_defaults(handler=verify_pair)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
