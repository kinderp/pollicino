# UDA 5 — L02 — materiale docente
## Training loop PyTorch

### Pipeline di riferimento
`batch -> model -> logits -> cross_entropy -> backward -> optimizer.step -> metrics`. La lezione deve essere debuggabile per strati.

### Checklist docente
- mini-batch con shape nota;
- loss finita;
- gradienti non nulli sui parametri attesi;
- parameter update verificabile;
- overfit su mini-corpus;
- save/load del checkpoint;
- evaluation in modalità coerente con il modello.

### Riproducibilità
Registrare seed, config, commit, backend e device. Distinguere riproducibilità scientifica da identità bit-per-bit: kernel e floating point possono produrre differenze minime pur lasciando valido il confronto.

### Collegamento a POLLICINO
PyTorch sarà la reference implementation iniziale. Non dobbiamo legare la specifica matematica alle API: le API possono cambiare, mentre shape, causalità, objective e metriche devono restare stabili.

**Nota:** durante il corso verificare sempre la documentazione ufficiale della versione PyTorch effettivamente installata.
