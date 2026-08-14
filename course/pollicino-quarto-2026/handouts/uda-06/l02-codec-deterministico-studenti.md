# POLLICINO — UDA 6, Lezione 02
## Encoder/decoder deterministico e round-trip byte-perfect

**Domanda guida:** come ricostruisce il decoder il prossimo byte se non possiede il file originale?

### Teoria
Il decoder ricostruisce la sequenza un byte alla volta. Dopo ogni prefisso già decodificato esegue lo stesso modello dell'encoder, ricostruisce la stessa distribuzione discreta e usa il range coder per determinare il simbolo successivo.

Questo rende il codec molto sensibile alle divergenze. Una differenza nella quantizzazione delle probabilità, nell'ordine dei simboli o nello stato del modello può cambiare un byte e far divergere tutto il resto.

### Contratto lossless
La proprietà fondamentale è `decode(encode(x)) == x` per ogni input supportato. Non “quasi uguale”: identico byte per byte.

### Micro-esperimento
Prima implementa encoder/decoder con un modello statico o bigramma. Testa file vuoto, run lunghi, tutti i 256 byte e input casuali. Poi collega il modello neurale.

### Problema numerico
Se encoder e decoder calcolano logits floating point leggermente diversi, una conversione ingenua in CDF può divergere. Il formato deve quindi specificare una discretizzazione deterministica o una via di inferenza controllata.

### Ponte
Solo dopo round-trip stabile ha senso misurare il vero rapporto di compressione.
