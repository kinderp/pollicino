# POLLICINO — UDA 5, Lezione 04
## Portare il byte model in MLX

**Domanda guida:** come portiamo lo stesso esperimento su Apple Silicon senza cambiare la domanda scientifica?

### Principio
PyTorch e MLX possono esprimere gli stessi oggetti matematici con API e modelli di esecuzione diversi. Il porting corretto parte quindi dalla **specifica**: vocab 256, shape, context length, layer, mask, loss e optimizer.

L'obiettivo non è tradurre riga per riga. Dobbiamo ottenere un modello equivalente nel significato, con differenze numeriche spiegabili.

### Checklist di equivalenza
- stessa architettura logica;
- stesso numero di parametri o differenze documentate;
- input `(B,T)` e logits `(B,T,256)`;
- stessa causalità;
- stessa definizione di loss;
- stesso dataset/split.

### Micro-esperimento
Implementa la configurazione tiny in MLX. Verifica shape e overfit sul mini-corpus. Registra validation bpb, throughput e memoria insieme alle differenze di dtype o inizializzazione.

### Errori da evitare
- backend più veloce non implica modello più accurato;
- differenze floating point minime non sono automaticamente bug;
- porting non significa copia sintattica.

### Ponte
Con due backend possiamo costruire un benchmark che separi qualità predittiva e costo computazionale.
