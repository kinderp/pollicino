# UDA 3 — L03 — materiale docente
## Loss, gradiente e backpropagation

### Formalizzazione
Dato un vettore di parametri `theta`, un passo SGD elementare è `theta_{k+1}=theta_k-eta∇L(theta_k)`. Separare chiaramente: (1) obiettivo, (2) calcolo del gradiente, (3) regola di aggiornamento.

La backpropagation è applicazione efficiente della regola della catena sul grafo computazionale. Il framework non indovina gli aggiornamenti: deriva operazioni note e accumula gradienti.

### Strategia didattica
Usare prima una funzione in una dimensione, disegnata su carta. Far sperimentare learning rate troppo piccolo e troppo grande. Solo dopo introdurre autodiff.

### Collegamento a POLLICINO
La loss è la stessa NLL/cross-entropy già interpretata come costo in bit. Questo è il punto in cui il corso unisce definitivamente informazione e apprendimento: diminuire la cross-entropy significa aumentare la probabilità assegnata ai byte corretti.

### Errori tipici
- `backward()` scambiato per update;
- confondere learning rate e gradiente;
- valutare il modello solo sul training.
