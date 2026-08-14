# UDA 4 — L02 — materiale docente
## Scaled dot-product self-attention

### Formalizzazione
Da input `X` otteniamo `Q=XW_Q`, `K=XW_K`, `V=XW_V`. I punteggi sono `S=QK^T/sqrt(d_k)` e l'output `softmax(S)V`. In self-attention tutte le proiezioni derivano dallo stesso flusso di rappresentazioni.

### Strategia
Lavorare inizialmente con T=3 e dimensione 2. Il corso deve far vedere matrici e shape, non affidarsi subito a una funzione di libreria. Solo dopo il caso manuale usare la primitive del backend.

### Caveat
I pesi di attention sono utili per ispezione ma non vanno presentati come spiegazione causale completa. La self-attention non è intrinsecamente causale: la mask è un'operazione separata.

### Collegamento scientifico
Test di shape e casi numerici minuscoli saranno parte della reference implementation. Un errore in Q/K/V o nel fattore di scala può non produrre crash ma degradare il training.

**Riferimento:** Vaswani et al., *Attention Is All You Need* (2017).
