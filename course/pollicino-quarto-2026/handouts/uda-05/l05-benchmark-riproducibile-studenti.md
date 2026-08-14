# POLLICINO — UDA 5, Lezione 05
## Benchmark PyTorch/MLX e scheda esperimento

**Domanda guida:** come confrontiamo due backend senza confondere velocità, qualità del modello e configurazione?

### Regola del benchmark
Prima di misurare decidiamo che cosa tenere fisso: corpus, split, architettura, context length, batch o budget di training. Poi separiamo le metriche:
- qualità: validation/test bpb;
- velocità: tempo e throughput;
- risorse: memoria;
- distribuzione: dimensione modello e dipendenze.

### Esempio
Dire “backend A è più veloce” senza hardware, batch, dtype e modello è incompleto. Dire “A produce 4,8 bpb e B 4,9” senza seed e budget di training è ugualmente incompleto.

### Scheda run
Per ogni esperimento registra almeno: commit, backend, device, seed, config, dataset manifest, numero di step, best validation bpb, tempo e note.

### Micro-esperimento
Esegui la stessa configurazione tiny su PyTorch e MLX. Non cercare un vincitore universale: scrivi una conclusione limitata alla configurazione osservata.

### Linguaggio scientifico
Preferisci “in questa configurazione abbiamo osservato...” a “X è sempre migliore di Y”.

### Ponte
UDA 6 userà il modello non solo per produrre probabilità, ma per costruire un bitstream lossless reale.
