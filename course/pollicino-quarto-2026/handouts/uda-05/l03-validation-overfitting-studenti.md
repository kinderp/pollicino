# POLLICINO — UDA 5, Lezione 03
## Validation, overfitting e scelta del checkpoint

**Domanda guida:** se la training loss continua a scendere, come capiamo se il modello sta diventando davvero migliore?

### Teoria
La training loss misura i dati usati per aggiornare i pesi. La validation loss misura dati non usati nello step. Se train migliora ma validation peggiora, il modello sta specializzandosi troppo: è un segnale di **overfitting**.

Il miglior checkpoint non è quindi necessariamente l'ultimo. Possiamo conservare quello che ottiene la migliore validation loss o validation bpb.

### Esempio
Un modello può memorizzare un file piccolo fino a quasi 0 bpb sul training e restare vicino alla baseline su file nuovi. Per un compressore generale non è un successo.

### Micro-esperimento
Disegna train e validation bpb durante il training. Salva il best checkpoint. Confronta due capacità del modello e annota quando le curve iniziano a divergere.

### Regola importante
Il test set non va usato ripetutamente per scegliere architettura, learning rate o durata: altrimenti diventa di fatto una seconda validation.

### Ponte
Con una reference controllata possiamo portare la stessa specifica su MLX.
