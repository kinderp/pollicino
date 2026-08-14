# UDA 6 — L04 — materiale docente
## Ablation e riproducibilità

### Obiettivo metodologico
Trasformare “proviamo cose” in esperimenti. Ogni run deve avere una domanda, una variabile modificata, controlli sufficienti e una metrica scelta prima di guardare il risultato.

### Riproducibilità
Conservare commit, config, corpus manifest, split, seed, backend/versioni, log, metriche e artifact. “Il codice gira” non basta se non sappiamo ricreare le condizioni della run.

### Risultati negativi
Devono restare nel registro: evitano di ripetere tentativi e riducono il rischio di raccontare soltanto le prove favorevoli.

### Caveat
A scuola non serve introdurre statistica inferenziale completa, ma bisogna insegnare prudenza: una differenza piccola su una singola run non giustifica una conclusione universale.

### Collegamento a POLLICINO
Le ablation su context, depth, width e CDF possono guidare l'architettura scientifica. Il registro esperimenti diventa memoria tecnica del progetto.
