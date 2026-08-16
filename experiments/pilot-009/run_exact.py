from __future__ import annotations

import importlib.util
from pathlib import Path

from exact_checkpoint import load_exact_checkpoint

HERE = Path(__file__).resolve().parent


def load_core():
    spec = importlib.util.spec_from_file_location("pilot009_core", HERE / "run.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    core = load_core()
    original_load_module = core.load_module

    def patched_load_module(path: Path, name: str):
        module = original_load_module(path, name)
        if path.parent.name == "pilot-005" and path.name == "run.py":
            module.prepare_frozen_model = load_exact_checkpoint
        return module

    core.load_module = patched_load_module
    core.main()


if __name__ == "__main__":
    main()
