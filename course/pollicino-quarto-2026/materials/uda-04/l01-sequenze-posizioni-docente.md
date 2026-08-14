# UDA 4 — L01 — materiale docente
## Sequenze, posizione e causalità

### Formalizzazione
Una rappresentazione iniziale semplice è `h_t = E[x_t] + P[t]`. Il modello autoregressivo fattorizza la probabilità della sequenza come prodotto di `P(x_t | x_<t)`: questa fattorizzazione giustifica il vincolo causale.

### Focus didattico
Far disegnare la matrice di visibilità prima di introdurre Q/K/V. È importante distinguere **context length** e dipendenza reale: limitare il contesto a T significa solo che il modello non può usare informazioni più lontane in quella configurazione.

### Collegamento a POLLICINO
Context length influenza bpb, memoria e throughput. Sarà quindi una variabile sperimentale dell'UDA 6, non un valore neutro.

### Misconcezioni
- embedding del token = embedding della posizione;
- contesto più lungo sempre migliore;
- training parallelo incompatibile con causalità.

### Risultato atteso
Lo studente deve saper motivare perché servono posizione e maschera causale prima ancora di vedere la formula dell'attention.
