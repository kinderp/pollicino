# POLLICINO — UDA 3, Lezione 02
## Softmax: da 256 logits a una distribuzione

**Domanda guida:** come trasformiamo punteggi arbitrari in 256 probabilità positive che sommano a uno?

### Teoria
Softmax prende un vettore di logits `z` e produce una distribuzione:
`p_i = exp(z_i) / sum_j exp(z_j)`.
I logits più alti ricevono probabilità maggiore, ma tutti gli elementi contribuiscono alla normalizzazione.

Aggiungere la stessa costante a tutti i logits non cambia il risultato. Per questo l'implementazione numericamente stabile sottrae `max(z)` prima di calcolare gli esponenziali: non è un'approssimazione, è una trasformazione equivalente che evita overflow.

### Esempio
Con logits `[2,1,0]` il primo simbolo è il più probabile, ma gli altri non spariscono. Con logits tutti uguali otteniamo una distribuzione uniforme: nel nostro alfabeto byte-level significa `1/256` per ogni byte e quindi la baseline di 8 bpb.

### Micro-esperimento
Implementa softmax in Python prima in forma diretta e poi sottraendo il massimo. Prova logits piccoli e molto grandi; verifica sempre che la somma delle probabilità sia circa 1.

### Errori da evitare
- softmax non “sceglie” il byte: produce una distribuzione;
- probabilità alta non significa automaticamente buona calibrazione;
- sottrarre il massimo non modifica la distribuzione matematica.

### Ponte
Ora possiamo misurare quanto è buona la probabilità assegnata al byte corretto usando la cross-entropy.
