# UDA 3 — laboratorio operativo

La UDA 3 sostituisce progressivamente le tabelle statistiche con **parametri appresi** senza usare ancora framework ML.

```text
funzione affine -> logits -> softmax -> cross-entropy
-> gradiente -> embedding -> MLP next-byte
```

Tutti i laboratori sono CPU-only e usano la sola libreria standard Python. L05 contiene volutamente un mini backprop manuale: non è l'implementazione più veloce, ma rende visibile ciò che PyTorch automatizzerà nella UDA 5.

Per lo studente:

```bash
python -m unittest discover -s tests -v
```

Test nascosti e soluzione hanno visibilità `teacher`.
