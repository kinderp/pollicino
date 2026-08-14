# UDA 5 — L05 — materiale docente
## Benchmark cross-backend

### Tre assi separati
1. **model quality:** NLL/bpb;
2. **compute cost:** tempo, throughput, memoria;
3. **deployment cost:** pesi, dipendenze, portabilità.

Un benchmark che modifica contemporaneamente modello e backend non consente attribuzione causale.

### Scheda esperimento minima
Commit, corpus manifest, split, config completa, seed, backend/versione, device, dtype, step/epoch, best validation metric, tempi e note su warmup o anomalie.

### Obiettivo didattico
Insegnare che il benchmark è un protocollo prima di essere un numero. Far scrivere la conclusione prima in forma assoluta e poi correggerla con condizioni e limiti.

### Collegamento a POLLICINO
Questa scheda può diventare il formato del registro esperimenti e la base delle ablation. In UDA 6 aggiungeremo metriche del codec reale e round-trip.
