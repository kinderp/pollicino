# UDA 5 — L01 — materiale docente
## Dataset, split e batch

### Specifica
Input e target sono indici interi in `[0,255]`; tipicamente `x.shape=y.shape=(B,T)`. Il target è shiftato di una posizione rispetto al contesto.

### Punto metodologico
La definizione dello split è parte dell'esperimento. Per dati compressivi è facile introdurre leakage tramite finestre sovrapposte, duplicati o versioni dello stesso file. Preferire quando possibile split per file/categoria e conservare un manifest con hash.

### Strategia
Far costruire prima un dataset da una stringa di pochi byte. Poi mostrare perché finestre adiacenti non sono campioni indipendenti. Introdurre train/validation/test prima dell'optimizer.

### Collegamento a POLLICINO
Il corpus manifest dovrà diventare un artifact stabile della ricerca: percorso logico, hash, categoria e split. Un miglioramento senza identità del dataset non è riproducibile.

### Risultato atteso
Gli studenti devono saper spiegare perché un buon training loop con split sbagliato produce comunque una valutazione sbagliata.
