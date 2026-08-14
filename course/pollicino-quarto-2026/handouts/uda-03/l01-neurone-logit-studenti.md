# POLLICINO — UDA 3, Lezione 01
## Dal punteggio al logit: un neurone come funzione parametrica

**Domanda guida:** come può una macchina imparare una regola invece di memorizzare una tabella per ogni contesto?

### Obiettivi
- capire il ruolo di pesi e bias;
- distinguere un punteggio da una probabilità;
- vedere una rete come funzione parametrica, non come insieme di regole scritte a mano.

### Teoria
Un neurone artificiale elementare calcola una somma pesata degli input e aggiunge un bias. In forma vettoriale: `z = Wx + b`. I valori di `W` e `b` sono parametri modificabili dal training. Prima di softmax l'uscita viene chiamata **logit** o punteggio: può essere positivo, negativo o molto grande e non deve sommare a uno.

Il vantaggio rispetto a una tabella è la **condivisione dei parametri**: la stessa funzione viene applicata a molti esempi. Il modello può quindi imparare regolarità che ricorrono in contesti diversi.

### Esempio
Se descriviamo il contesto con tre caratteristiche e vogliamo produrre 256 punteggi, una matrice può combinare quelle caratteristiche in modo diverso per ciascun possibile byte successivo.

### Micro-esperimento
Implementa `z = w1*x1 + w2*x2 + b`, modifica manualmente i pesi e osserva l'uscita. Poi passa a una piccola matrice che produce più logits.

### Da ricordare
- un logit **non** è ancora una probabilità;
- più parametri non garantiscono generalizzazione;
- la metafora biologica è secondaria rispetto alla funzione matematica.

### Ponte
Nella prossima lezione trasformeremo i 256 logits in una distribuzione valida con softmax.
