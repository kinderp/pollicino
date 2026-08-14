# UDA 3 — L05 — materiale docente
## MLP next-byte

### Modello
Il modello approssima `q_theta(x_t | x_{t-k:t})`. Input: `k` indici byte; embedding e concatenazione; MLP; output 256 logits. Obiettivo: NLL del byte successivo.

### Valore didattico
Questa baseline neurale deve restare nel progetto anche quando il Transformer la supera. Permette di attribuire eventuali guadagni all'architettura e non semplicemente al fatto di aver usato una rete neurale.

### Esperimento minimo
Usare lo stesso split di uniforme/bigramma. Prima verificare overfit su un corpus minuscolo; poi passare al validation. Riportare bpb e parameter count.

### Misconcezioni
- “rete neurale” = contesto illimitato;
- singola run = conclusione definitiva;
- training loss = prestazione del codec.

### Ponte
La limitazione strutturale è il contesto fisso concatenato. L'attenzione dell'UDA 4 permetterà a ogni posizione di costruire dinamicamente una combinazione delle posizioni precedenti.

**Riferimento:** Bengio et al., *A Neural Probabilistic Language Model* (2003).
