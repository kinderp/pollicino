from __future__ import annotations

import importlib.util
import socket
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

# Some historical benchmark mirrors can be slow. This wrapper changes only the
# network read timeout; protocol, candidate grid, budgets and holdout are untouched.
socket.setdefaulttimeout(900)
_original_urlopen = urllib.request.urlopen


def _long_urlopen(url, *args, **kwargs):
    timeout = kwargs.get("timeout")
    if timeout is None or timeout < 900:
        kwargs["timeout"] = 900
    return _original_urlopen(url, *args, **kwargs)


urllib.request.urlopen = _long_urlopen

spec = importlib.util.spec_from_file_location("pilot011_core", Path(__file__).with_name("run.py"))
core = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(core)
core.main()
