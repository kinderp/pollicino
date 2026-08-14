# POLLICINO — UDA 4, Lezione 05
## Tiny Transformer byte-level completo

**Domanda guida:** possiamo assemblare tutti i pezzi in un modello che predice davvero il prossimo byte?

### Architettura
1. input: indici byte `(B,T)`;
2. token + positional embedding: `(B,T,C)`;
3. uno o più blocchi Transformer causali;
4. normalization finale;
5. proiezione verso 256 logits: `(B,T,256)`;
6. target: sequenza spostata di un byte `(B,T)`.

Il modello implementa `q_theta(x_t | x_<t)` e viene allenato con cross-entropy. La stessa loss può essere convertita in bpb.

### Micro-esperimento
Costruisci il modello più piccolo che esegue un forward. Aggiungi test di shape e causalità. Poi prova l'**overfit controllato** su un corpus minuscolo: se il modello non riesce nemmeno a memorizzare pochi esempi, probabilmente c'è un problema nella pipeline.

### Attenzione
Memorizzare un corpus minuscolo è un test diagnostico, non una misura di generalizzazione. Il confronto reale arriverà su validation/test.

### Checklist
- vocab size = 256;
- target correttamente shiftato;
- mask causale testata;
- logits con shape corretta;
- loss finita;
- gradienti presenti.

### Ponte
UDA 5 trasforma il prototipo in pipeline riproducibili PyTorch e MLX.
