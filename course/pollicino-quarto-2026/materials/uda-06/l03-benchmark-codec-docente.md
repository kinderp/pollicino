# UDA 6 — L03 — materiale docente
## Protocollo di benchmark del codec

### Prima del numero: definire lo scenario
Standalone, modello condiviso/preinstallato e corpus batch possono contabilizzare il costo dei pesi in modo diverso. Il report deve dichiarare lo scenario.

### Metriche
- compression size e ratio;
- real bpb;
- ideal model bpb;
- coder overhead;
- encode/decode latency;
- throughput;
- memoria;
- model size;
- round-trip.

### Metodo
Congelare corpus e versioni, usare gli stessi input per tutte le baseline, conservare hash degli originali e risultati. Separare misure di qualità e costo.

### Didattica
Far trovare agli studenti un benchmark scorretto e chiedere come correggerlo. È un buon esercizio di cittadinanza scientifica: numeri veri possono sostenere conclusioni false se il protocollo è sbagliato.

### Collegamento a POLLICINO
Il benchmark dovrà diventare automatizzato e ripetibile da CI o script dedicati quando il progetto matura.
