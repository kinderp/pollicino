# POLLICINO — UDA 5, Lezione 01
## Dataset byte-level, split e batch

**Domanda guida:** come trasformiamo file arbitrari in esempi di training senza falsare la valutazione?

### Teoria
Da una sequenza di byte creiamo coppie input/target. Con context length `T`, l'input contiene T byte e il target è la stessa finestra spostata di una posizione. Più finestre possono essere raccolte in un batch `(B,T)`.

La parte più importante non è soltanto costruire i tensori: dobbiamo separare **train**, **validation** e **test**. Il training modifica i pesi; la validation guida le scelte; il test deve restare il più possibile congelato fino alla valutazione finale.

### Esempio
Da `ABCDE` e context 3 possiamo ottenere `ABC -> BCD`. Finestre vicine sono però molto simili: se porzioni quasi identiche finiscono in train e test, il risultato può essere troppo ottimistico.

### Micro-esperimento
Implementa un dataset che restituisce `(x,y)`. Verifica valori 0..255, dtype intero e shape. Crea poi uno split per file o categoria e documentalo.

### Errori da evitare
- shuffle non elimina automaticamente il leakage;
- più finestre non significa più dati indipendenti;
- validation e test non hanno lo stesso ruolo.

### Ponte
Con una pipeline dati stabile possiamo scrivere il training loop PyTorch.
