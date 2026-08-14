# POLLICINO — UDA 4, Lezione 01
## Sequenze, contesto causale e posizione

**Domanda guida:** se l'embedding dice quale byte stiamo guardando, come fa il modello a sapere dove si trova nella sequenza?

### Teoria
Un Transformer elabora una finestra di più byte. L'embedding del simbolo non contiene l'ordine: le sequenze `ABC` e `CBA` usano gli stessi simboli ma hanno struttura diversa. Per questo aggiungiamo una rappresentazione della **posizione**.

Per il next-byte modeling esiste poi un vincolo ancora più importante: una previsione alla posizione `t` deve dipendere solo dai byte disponibili fino a quel punto. Il modello è quindi **causale**. Durante il training possiamo calcolare molte posizioni in parallelo, ma nessuna deve leggere il futuro.

### Esempio
Con rappresentazioni apprese possiamo scrivere `h_t = E[x_t] + P[t]`, dove `E` è l'embedding del byte e `P` quello della posizione.

### Micro-esperimento
Costruisci una sequenza di indici, applica token embedding e positional embedding e verifica la shape `(B,T,C)`. Disegna poi una matrice triangolare che indichi quali posizioni possono vedere quali altre.

### Da ricordare
- posizione e identità del byte sono informazioni diverse;
- la context window è un limite computazionale;
- causalità non significa necessariamente elaborazione lenta elemento per elemento durante il training.

### Ponte
La self-attention userà questa sequenza per scegliere dinamicamente quali posizioni precedenti sono più utili.
