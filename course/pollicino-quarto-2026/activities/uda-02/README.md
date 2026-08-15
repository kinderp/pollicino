# UDA 2 — Laboratori operativi

Questa cartella contiene gli activity package eseguibili della UDA 2 di POLLICINO.

## Progressione

1. `l01` — Run-Length Encoding: primo codec byte-level con round-trip.
2. `l02` — Huffman canonico: codici a prefisso, payload bit-packed e costo del codebook.
3. `l03` — modello zero-order: frequenze, probabilità, entropia e smoothing.
4. `l04` — n-gram/Markov: il contesto migliora la previsione del byte successivo.
5. `l05` — benchmark comune: uniform, 0/1/2/3-gram misurati in bits-per-byte su test separato.

## Regola scientifica

Ogni risultato deve distinguere dati usati per costruire il modello, dati usati per valutarlo, costo ideale del payload ed eventuale overhead necessario a rendere il formato realmente decodificabile.

Non si considera valida una compressione lossless senza verifica di round-trip quando esiste un encoder reale.

## Esecuzione

```bash
python -m unittest discover -s tests -v
python main.py
```

Tutti i laboratori usano soltanto la libreria standard Python.
