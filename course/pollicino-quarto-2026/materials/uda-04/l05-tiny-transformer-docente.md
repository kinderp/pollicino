# UDA 4 — L05 — materiale docente
## Tiny Transformer di riferimento

### Specifica concettuale
Il modello byte-level usa vocabolario 256, context length T, width C, positional information, N blocchi causali e una output head 256-way. La loss è la NLL del target successivo.

### Sanity checks prima del training serio
- shape end-to-end;
- test causale;
- loss iniziale compatibile con logits quasi uniformi;
- overfit su mini-corpus;
- serializzazione della config.

L'overfit controllato serve a verificare capacità e gradienti, non è un risultato del progetto.

### Ponte PyTorch/MLX
La specifica deve essere indipendente dal backend. In UDA 5 mapperemo gli stessi oggetti matematici sulle due librerie, accettando differenze numeriche ma non differenze di significato.

### Collegamento al codec
L'output 256-way è già esattamente l'interfaccia probabilistica che in UDA 6 alimenterà il range coder.

**Riferimento principale:** Vaswani et al. (2017), con adattamento causale byte-level.
