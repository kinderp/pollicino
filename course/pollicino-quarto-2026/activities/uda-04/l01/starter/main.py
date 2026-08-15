from __future__ import annotations

def add_vectors(a: list[float], b: list[float]) -> list[float]:
    # TODO: somma elemento per elemento e rifiuta dimensioni diverse.
    raise NotImplementedError

def combine_embeddings(token_rows: list[list[float]], position_rows: list[list[float]]) -> list[list[float]]:
    # TODO: a ogni token embedding aggiungi l'embedding della sua posizione.
    raise NotImplementedError

def causal_mask(length: int) -> list[list[bool]]:
    # TODO: la posizione i può vedere solo posizioni j <= i.
    raise NotImplementedError

def context_windows(data: bytes, context_length: int) -> list[tuple[bytes, int]]:
    # TODO: costruisci coppie (contesto passato, byte target).
    raise NotImplementedError
