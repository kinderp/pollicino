# UDA 1 — laboratorio operativo

Questa cartella contiene gli activity package eseguibili della UDA 1.

Ogni lezione usa la stessa convenzione:

```text
lNN/
├── starter/main.py
├── fixtures/
├── tests/test_public.py
└── teacher/
    ├── solution.py
    └── ../tests/test_hidden.py
```

Gli asset sono dichiarati nei file activity JSON secondo il contratto di `2cornot2c`.

## Per gli studenti

Dopo la creazione dello scaffold:

```bash
python -m unittest discover -s tests -v
```

I test pubblici devono passare prima della consegna. Tutte le attività della UDA 1 usano solo la libreria standard di Python.

## Per il docente

La soluzione di riferimento e i test nascosti hanno visibilità `teacher` e non devono entrare nel repository studente. Prima di pubblicare una revisione della UDA, eseguire i test pubblici e nascosti contro la soluzione docente.

## Obiettivo metodologico

Il laboratorio costruisce una catena unica:

```text
byte -> hash -> probabilità -> informazione -> entropia -> bits/byte
```

La UDA termina con due invarianti che resteranno validi per tutto POLLICINO:

1. una distribuzione uniforme sui 256 byte costa `8 bit/byte`;
2. ogni codec dichiarato lossless deve superare il controllo byte-perfect, idealmente verificato anche con SHA-256.
