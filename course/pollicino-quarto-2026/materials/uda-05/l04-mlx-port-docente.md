# UDA 5 — L04 — materiale docente
## Porting MLX

### Contratto di equivalenza
La specifica comune deve vivere sopra il backend: vocab, width, depth, heads, context, mask, objective, split e metriche. Il porting si giudica su questi invarianti, non sulla somiglianza del codice.

### Verifiche
- parameter count;
- shape di ogni stadio;
- causal mask;
- loss su casi sintetici;
- overfit sullo stesso mini-corpus;
- confronto di config e dtype.

### Differenze numeriche
Floating point, kernel e inizializzazioni possono divergere. Cercare invece differenze sistematiche: loss incompatibile, futuro visibile, target shift errato, parameter count inatteso.

### Collegamento a POLLICINO
MLX è particolarmente utile per sperimentazione locale su Apple Silicon; PyTorch resta una reference portabile. Il progetto deve poter confrontare i backend senza trasformarli in due architetture diverse.

**Nota:** usare durante il corso la documentazione ufficiale MLX della versione installata.
