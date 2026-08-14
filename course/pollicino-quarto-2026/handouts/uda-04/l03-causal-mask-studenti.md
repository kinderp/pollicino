# POLLICINO — UDA 4, Lezione 03
## Maschera causale e previsione autoregressiva

**Domanda guida:** come impediamo al modello di barare guardando il byte che deve ancora prevedere?

### Teoria
Durante il training conosciamo tutta la sequenza, compresi i target futuri. Senza una maschera l'attention potrebbe usare quei byte e ottenere una loss artificialmente bassa. La **causal mask** rende non selezionabili le posizioni future.

Per una sequenza di quattro posizioni, la posizione 0 vede solo 0; la posizione 1 vede 0 e 1; la posizione 2 vede 0,1,2. Prima della softmax aggiungiamo ai punteggi vietati un valore equivalente a `-infinito`, così il loro peso diventa zero.

### Micro-esperimento di debug
Crea due versioni della stessa attention: una senza mask e una con mask. Verifica automaticamente che tutti i pesi sopra la diagonale siano zero nella versione causale. Modifica intenzionalmente un byte futuro e controlla che l'output di una posizione precedente non cambi.

### Perché è importante
Un bug di leakage può far sembrare eccezionale un modello che in realtà non sa predire. È quindi un problema sia di codice sia di metodo scientifico.

### Ponte
Con causalità corretta possiamo costruire più teste e il blocco Transformer completo.
