# POLLICINO — UDA 3, Lezione 05
## Primo modello neurale next-byte: embedding + MLP

**Domanda guida:** possiamo battere una baseline statistica con una piccola rete che guarda una finestra di byte?

### Teoria
Prendiamo gli ultimi `k` byte, recuperiamo i loro embedding, li concateniamo e li passiamo a una MLP. L'ultimo strato produce 256 logits; softmax li interpreta come distribuzione del prossimo byte; la cross-entropy aggiorna tutti i parametri.

Con contesto di 4 byte e embedding 16, l'MLP riceve 64 valori. A differenza di una tabella di trigrammi o 4-grammi, i parametri sono condivisi tra moltissimi contesti.

### Micro-esperimento
Costruisci coppie `(context,target)`, addestra una rete piccola e misura train e validation bpb. Confronta sulla stessa validation: uniforme, bigramma e MLP. Conserva seed e configurazione.

### Cosa osservare
- il modello può migliorare sul training e peggiorare sul validation;
- una finestra `k` resta un limite rigido del contesto;
- bpb è la stessa metrica usata per i modelli statistici.

### Exit ticket
Spiega perché questa MLP è già un language model byte-level, pur non essendo un Transformer.

### Ponte
UDA 4 sostituisce la finestra rigida con self-attention causale.
