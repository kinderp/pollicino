# UDA 4 — L04 — materiale docente
## Il blocco Transformer

### Specifica didattica
Adottare una sola variante di riferimento per evitare dispersione: pre-norm, causal self-attention, MLP e residual. Le varianti architetturali vanno annotate ma non mischiate durante la prima implementazione.

### Shape invariants
Input e output del blocco restano `(B,T,C)`. Se `C` è diviso tra `H` heads, la dimensione per head deve essere coerente con la scelta progettuale. Contare parametri delle proiezioni QKV, output projection, MLP e norm.

### Perché le componenti servono
- multi-head: più sottospazi di relazione;
- residual: percorso additivo e flusso del segnale;
- norm: controllo delle scale;
- MLP: trasformazione non lineare posizione-per-posizione.

### Collegamento alla ricerca
Numero di layer, heads, width e rapporto MLP saranno iperparametri. Ogni ablation deve cambiare una cosa alla volta e mantenere registrata la configurazione.

### Caveat
Non presentare le teste come interpretabili per definizione. L'attenzione è un meccanismo computazionale, non un'etichetta semantica.
