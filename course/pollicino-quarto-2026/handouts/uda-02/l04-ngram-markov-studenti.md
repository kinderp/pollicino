# POLLICINO — UDA 2, Lezione 04
## Contesto, n-gram e modelli di Markov

**Domanda guida:** Il prossimo byte dipende soltanto da quanto è frequente in generale, o anche da ciò che lo precede?

### Obiettivi
- Comprendere il concetto centrale della lezione e collegarlo alla compressione lossless.
- Saper leggere o costruire un piccolo esempio numerico o di codice.
- Saper spiegare che cosa misura l'esperimento e quali conclusioni sono lecite.

### Perché ci serve in POLLICINO

Dalle ridondanze visibili ai modelli probabilistici di contesto. In questa lezione lavoriamo su **Contesto, n-gram e modelli di Markov**. Il criterio resta sempre lo stesso: ogni nuova idea deve aiutarci a descrivere i byte in modo più corto senza perdere la possibilità di ricostruirli esattamente.

### Idea fondamentale

Un modello zero-order usa una sola distribuzione per tutto il file. Un modello bigramma usa invece il byte precedente come contesto: dopo ogni possibile byte mantiene una distribuzione diversa del byte successivo. Un trigramma usa gli ultimi due byte, e così via. Più contesto può rendere la previsione più precisa, ma aumenta rapidamente il numero di combinazioni da stimare.

### Esempio ragionato

Nel testo, dopo la lettera `q` è molto più probabile vedere `u` che una lettera casuale. A livello byte, pattern analoghi compaiono anche in header, sorgenti, markup e strutture binarie. Il contesto cambia la distribuzione: la probabilità è condizionata.

### Esperimento guidato

Costruisci un contatore bigramma 256x256. Per ogni byte precedente, stima la distribuzione del successivo con smoothing. Calcola la cross-entropy sul file di test. Se vuoi estendere, prova trigrammi con un dizionario sparso e confronta memoria e qualità.

Durante l'esperimento conserva almeno input, configurazione e risultato. Se produci un encoder o un decoder, il controllo più importante è il **round-trip**: ciò che decodifichi deve essere identico, byte per byte, all'originale.

### Che cosa osservare

Non limitarti a dire “funziona” o “non funziona”. Chiediti:
- quale informazione usa il metodo;
- quale costo introduce;
- su quali dati sembra funzionare meglio;
- se il risultato vale sul training, sul test o su entrambi;
- come cambierebbe il risultato usando un contesto o un modello diverso.

### Errori da evitare

- più n significa sempre modello migliore.
- un n-gram comprende il significato.
- un modello con loss più bassa sul training generalizza automaticamente.

### Esercizi

1. Spiega con parole tue la risposta alla domanda guida: **Il prossimo byte dipende soltanto da quanto è frequente in generale, o anche da ciò che lo precede?**
2. Individua un caso in cui l'idea della lezione potrebbe fallire o essere poco utile.
3. Collega il concetto a una delle metriche già usate in POLLICINO: dimensione, probabilità, loss o bits-per-byte.

### Exit ticket

In massimo cinque righe scrivi:
1. qual è l'input del metodo visto oggi;
2. qual è il suo output;
3. quale misura useresti per capire se è utile a POLLICINO.

### Verso la prossima lezione

Abbiamo un vero predittore. Ora possiamo confrontare tutti i modelli con una misura unica: cross-entropy in bit per byte.
