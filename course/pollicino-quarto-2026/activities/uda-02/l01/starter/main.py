from __future__ import annotations

from pathlib import Path


def rle_encode(data: bytes) -> bytes:
    """Encode bytes as (count, value) pairs with count in 1..255."""
    # TODO 1: gestisci il caso vuoto.
    # TODO 2: scorri i byte raggruppando run uguali.
    # TODO 3: ricorda che il conteggio entra in un solo byte: massimo 255.
    raise NotImplementedError


def rle_decode(encoded: bytes) -> bytes:
    """Decode a stream of (count, value) pairs."""
    # TODO 4: ogni coppia è (conteggio, valore).
    # Rifiuta stream di lunghezza dispari e conteggi uguali a zero.
    raise NotImplementedError


def compression_ratio(original: bytes, encoded: bytes) -> float:
    """Return encoded/original size. Empty input has ratio 1.0."""
    # TODO 5: ratio = dimensione codificata / dimensione originale.
    raise NotImplementedError


def savings_percent(original: bytes, encoded: bytes) -> float:
    if not original:
        return 0.0
    return 100.0 * (1.0 - compression_ratio(original, encoded))


def analyze_file(path: Path) -> dict[str, float | int | bool]:
    data = path.read_bytes(); encoded = rle_encode(data); decoded = rle_decode(encoded)
    return {"original_bytes":len(data),"encoded_bytes":len(encoded),"ratio":compression_ratio(data,encoded),"savings_percent":savings_percent(data,encoded),"roundtrip_ok":decoded==data}


def main() -> None:
    for filename in ("fixtures/repetitive.txt", "fixtures/mixed.txt", "fixtures/nonrepetitive.txt"):
        print(filename, analyze_file(Path(filename)))


if __name__ == "__main__":
    main()
