# UDA 3 — L04 — materiale docente
## Embedding byte-level

### Formalizzazione
`E ∈ R^(256×d)`. Per un indice `x_t`, la rappresentazione iniziale è la riga `E[x_t]`. L'operazione è una lookup parametrica ed è equivalente a `one_hot(x_t) E`.

### Scelta byte-level
Questa lezione è importante per POLLICINO perché il vocabolario di 256 simboli è totale su qualunque file: nessun tokenizer esterno e nessun problema di reversibilità della tokenizzazione. Il prezzo è una sequenza più lunga rispetto a tokenizzazioni di livello superiore.

### Strategia
Mostrare prima one-hot di 4 simboli, poi generalizzare a 256. Far contare i parametri `256*d`. Non attribuire semantica forte alle distanze: può essere un'esplorazione, non una prova.

### Risultato atteso
Lo studente deve comprendere shape, lookup e motivo per cui l'indice grezzo non è una feature continua adeguata.

### Ponte scientifico
Gli stessi embedding saranno l'ingresso del tiny Transformer dell'UDA 4.
