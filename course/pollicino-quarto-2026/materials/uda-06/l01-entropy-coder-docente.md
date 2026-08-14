# UDA 6 — L01 — materiale docente
## Entropy coding e range coding

### Nucleo scientifico
La NLL totale `-Σ log2 q(x_t|x_<t)` è un limite/costo ideale del modello, non il file compresso. Un arithmetic/range coder materializza un codice vicino a quel costo usando CDF discrete e renormalization.

### Strategia didattica
Prima lavorare con intervalli reali su un alfabeto minuscolo; poi spiegare perché un'implementazione reale preferisce aritmetica intera o una rappresentazione controllata. Tenere sempre separati **model quality** e **coder efficiency**.

### Collegamento a POLLICINO
Il Transformer produrrà una distribuzione 256-way; un adattatore dovrà trasformarla in frequenze cumulative valide per il coder. Questo adattatore è parte del formato e deve essere deterministico.

### Misconcezioni
- bpb della loss = byte del file reale;
- probabilità floating point possono essere ricostruite “abbastanza simili” dal decoder;
- il range coder aggiunge capacità predittiva.

**Riferimento:** Witten, Neal, Cleary, *Arithmetic Coding for Data Compression* (1987), più documentazione del coder scelto durante l'implementazione.
