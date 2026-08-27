from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile


UPSTREAM = "https://github.com/bitcoin-core/minisketch.git"
COMMIT = "4a179c61e3cbe3ac2b3c027764ce8eb5183155e1"


def main() -> None:
    root = Path(__file__).resolve().parent
    destination = root / "lib" / "minisketch"
    if destination.exists():
        shutil.rmtree(destination)
    (destination / "include").mkdir(parents=True)
    (destination / "src" / "fields").mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="pollicino-minisketch-") as tmp:
        checkout = Path(tmp) / "minisketch"
        subprocess.run(
            ["git", "clone", "--quiet", UPSTREAM, str(checkout)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(checkout), "checkout", "--quiet", COMMIT],
            check=True,
        )

        shutil.copy2(checkout / "include" / "minisketch.h", destination / "include")
        shutil.copy2(checkout / "src" / "minisketch.cpp", destination / "src")
        for source in (checkout / "src").glob("*.h"):
            shutil.copy2(source, destination / "src")
        for source in (checkout / "src" / "fields").glob("generic_*.cpp"):
            shutil.copy2(source, destination / "src" / "fields")
        for source in (checkout / "src" / "fields").glob("*.h"):
            shutil.copy2(source, destination / "src" / "fields")

    (destination / "UPSTREAM_PIN.txt").write_text(
        f"{UPSTREAM}\n{COMMIT}\n",
        encoding="utf-8",
    )
    print(f"prepared libminisketch {COMMIT} in {destination}")


if __name__ == "__main__":
    main()
