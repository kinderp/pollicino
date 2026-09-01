# PX3-PN-D2 deterministic local experiment

This directory records the generic bounded reference catalog's deterministic
local accounting and A/B/C method-call simulation. Run from the repository root:

```bash
PYTHONPATH=src python experiments/px3-pn-d2/run.py
```

The run performs no network operation and no performance benchmark. All byte
figures are `MODEL_PROTOCOL_ACCOUNTING_ONLY`; the encoding model is documented
inside `catalog-matrix.json`. Generated JSON is sorted and contains no clock or
host-dependent field.

