# POLLICINO — UDA 6, Lezione 03
## Benchmark reale: payload, header, modello e baselines

**Domanda guida:** quando possiamo dire davvero che POLLICINO comprime meglio di una baseline?

### Teoria
Il bpb del modello è un costo ideale. Il benchmark del codec misura invece i byte realmente prodotti. Dobbiamo dichiarare che cosa includiamo: payload, header, tabelle, configurazione e — a seconda dello scenario — costo del modello.

Un modello da molti megabyte che comprime bene un file piccolo può essere inutile in modalità standalone ma interessante se il modello è preinstallato e condiviso tra molti file. Sono scenari diversi e vanno descritti separatamente.

### Tabella minima
Per ogni file registra:
- byte originali e compressi;
- bpb ideale e bpb reale;
- encode/decode time;
- peak memory se disponibile;
- esito del round-trip;
- baseline usate.

### Micro-esperimento
Confronta raw, una baseline statistica del corso, un compressore classico disponibile e POLLICINO sullo stesso corpus. Non selezionare soltanto i file favorevoli.

### Errori da evitare
- escludere overhead senza dichiararlo;
- confrontare file o condizioni diverse;
- usare un solo file come prova di una categoria.

### Ponte
Con un benchmark corretto possiamo fare ablation per capire da dove viene ogni miglioramento.
