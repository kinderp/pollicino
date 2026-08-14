# POLLICINO — UDA 3, Lezione 03
## Cross-entropy, gradiente e discesa del gradiente

**Domanda guida:** come sappiamo in quale direzione modificare i pesi per rendere migliore la previsione?

### Teoria
La loss misura l'errore del modello. Il **gradiente** raccoglie le derivate della loss rispetto ai parametri e ci dice come cambierebbe la loss per piccole variazioni dei pesi. La discesa del gradiente usa l'aggiornamento elementare `theta <- theta - eta * grad(L)`, dove `eta` è il learning rate.

La **backpropagation** non è l'algoritmo di ottimizzazione: è il modo efficiente con cui calcoliamo i gradienti attraverso una catena di operazioni. L'optimizer usa poi quei gradienti per aggiornare i parametri.

### Esempio
Per `L(w)=(w-3)^2`, partendo da `w=0` il gradiente indica che dobbiamo aumentare `w`. Ripetendo piccoli passi ci avviciniamo al minimo.

### Micro-esperimento
Ottimizza a mano o con Python un solo parametro su una parabola. Poi usa un framework su un classificatore minuscolo: stampa loss prima e dopo alcuni step.

### Da ricordare
- il gradiente non garantisce il minimo globale;
- backpropagation e gradient descent sono concetti diversi;
- training loss che scende non basta a dimostrare generalizzazione.

### Ponte
Per usare i byte come input del modello dobbiamo rappresentarli come vettori imparabili: gli embedding.
