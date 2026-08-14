# POLLICINO — UDA 4, Lezione 02
## Self-attention: query, key e value

**Domanda guida:** come può una posizione decidere quali byte precedenti sono più utili per la previsione corrente?

### Teoria
La self-attention costruisce tre rappresentazioni di ogni posizione: **query**, **key** e **value**. La query della posizione corrente viene confrontata con le key delle altre posizioni. I prodotti scalari producono punteggi di compatibilità; softmax li trasforma in pesi; la media pesata dei value produce una nuova rappresentazione.

La formula compatta è `Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V`. Il fattore `sqrt(d_k)` mantiene i punteggi in una scala più gestibile.

### Esempio
Una posizione può assegnare più peso a un byte precedente che ricorre in un pattern utile. Non dobbiamo però interpretare automaticamente quel peso come spiegazione completa del ragionamento del modello.

### Micro-esperimento
Usa tensori molto piccoli. Stampa Q, K, V, matrice dei punteggi, pesi softmax e output. Verifica le shape prima di aggiungere batch e sequenze più lunghe.

### Errori da evitare
- Q, K e V non sono tre sequenze esterne diverse;
- attention da sola non impedisce di guardare il futuro;
- i pesi di attention non sono una spiegazione perfetta del modello.

### Ponte
Nella prossima lezione aggiungeremo la causal mask per impedire il leakage del target.
