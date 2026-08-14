# POLLICINO — UDA 3, Lezione 04
## Embedding: imparare una rappresentazione dei byte

**Domanda guida:** perché non basta usare direttamente i numeri 0–255 come grandezze continue?

### Teoria
L'indice numerico di un byte è un'etichetta: `200` non è “due volte più simile” a `100` di quanto lo sia `0`. Un **embedding** associa invece a ciascuno dei 256 byte un vettore di numeri reali che viene appreso durante il training.

Possiamo immaginare una matrice `E` con 256 righe e `d` colonne. L'indice del byte seleziona una riga. È equivalente concettualmente a moltiplicare un vettore one-hot per la matrice, ma una lookup è più efficiente.

### Esempio
Con dimensione `d=16`, ogni byte è trasformato in 16 numeri. Una sequenza di `T` byte diventa una sequenza di `T` vettori.

### Micro-esperimento
Crea una matrice di embedding e seleziona le righe corrispondenti a una piccola sequenza. Verifica le shape. Dopo un mini-training puoi esplorare distanze tra embedding, senza attribuire automaticamente significati umani alle dimensioni.

### Errori da evitare
- l'embedding non contiene da solo la posizione;
- byte numericamente vicini non devono avere vettori vicini;
- le dimensioni non hanno necessariamente interpretazione stabile.

### Ponte
Concateneremo gli embedding di una piccola finestra e costruiremo il primo predittore neurale next-byte.
