# UDA 4 — L03 — materiale docente
## Causal mask e leakage

### Formalizzazione
`A = softmax(S + M)`, con `M_ij=0` se `j<=i` e valore molto negativo se `j>i`. La mask realizza computazionalmente la fattorizzazione autoregressiva.

### Obiettivo didattico
Usare questa lezione come caso di **data leakage**. Una loss molto bassa non è prova sufficiente di qualità: bisogna verificare che il protocollo impedisca accesso al target.

### Test consigliati
- matrice di attention nulla sopra la diagonale;
- perturbazione del futuro che non cambia output passati;
- confronto tra implementazione manuale e primitive causali del backend.

### Misconcezioni
- mask necessaria solo in inference;
- teacher forcing = uso illegittimo del futuro;
- assenza di errori runtime = causalità corretta.

### Collegamento a POLLICINO
Questo test deve restare permanente nel repository perché un regressione della mask invaliderebbe bpb, benchmark e codec.
