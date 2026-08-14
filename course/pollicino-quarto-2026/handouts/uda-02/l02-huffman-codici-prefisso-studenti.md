# POLLICINO — UDA 2, Lezione 02
## Huffman e codici a prefisso

**Domanda guida:** Se alcuni simboli compaiono più spesso, perché dovrebbero occupare lo stesso numero di bit degli altri?

### Obiettivi
- Comprendere il concetto centrale della lezione e collegarlo alla compressione lossless.
- Saper leggere o costruire un piccolo esempio numerico o di codice.
- Saper spiegare che cosa misura l'esperimento e quali conclusioni sono lecite.

### Perché ci serve in POLLICINO

Dalle ridondanze visibili ai modelli probabilistici di contesto. In questa lezione lavoriamo su **Huffman e codici a prefisso**. Il criterio resta sempre lo stesso: ogni nuova idea deve aiutarci a descrivere i byte in modo più corto senza perdere la possibilità di ricostruirli esattamente.

### Idea fondamentale

Un codice a lunghezza fissa assegna lo stesso numero di bit a ogni simbolo. Huffman usa invece codici più corti per i simboli frequenti e più lunghi per quelli rari. La proprietà di prefisso garantisce che nessun codice valido inizi con un altro codice valido: il decoder può quindi leggere il flusso senza separatori speciali.

### Esempio ragionato

Immagina quattro simboli con frequenze A=50, B=25, C=15, D=10. Una codifica fissa richiede 2 bit per simbolo. Un albero di Huffman può assegnare ad A un codice molto corto e spostare i simboli rari più in profondità. Il costo medio diventa una media pesata dalle probabilità.

### Esperimento guidato

Calcola le frequenze dei byte di un piccolo file, costruisci l'albero combinando ogni volta i due nodi meno frequenti, genera la tabella dei codici e misura il numero totale di bit teorici. Se implementi encoder e decoder, aggiungi la verifica round-trip.

Durante l'esperimento conserva almeno input, configurazione e risultato. Se produci un encoder o un decoder, il controllo più importante è il **round-trip**: ciò che decodifichi deve essere identico, byte per byte, all'originale.

### Che cosa osservare

Non limitarti a dire “funziona” o “non funziona”. Chiediti:
- quale informazione usa il metodo;
- quale costo introduce;
- su quali dati sembra funzionare meglio;
- se il risultato vale sul training, sul test o su entrambi;
- come cambierebbe il risultato usando un contesto o un modello diverso.

### Errori da evitare

- il simbolo più frequente ha sempre codice 0.
- l'albero di Huffman è unico.
- Huffman usa il contesto precedente.

### Esercizi

1. Spiega con parole tue la risposta alla domanda guida: **Se alcuni simboli compaiono più spesso, perché dovrebbero occupare lo stesso numero di bit degli altri?**
2. Individua un caso in cui l'idea della lezione potrebbe fallire o essere poco utile.
3. Collega il concetto a una delle metriche già usate in POLLICINO: dimensione, probabilità, loss o bits-per-byte.

### Exit ticket

In massimo cinque righe scrivi:
1. qual è l'input del metodo visto oggi;
2. qual è il suo output;
3. quale misura useresti per capire se è utile a POLLICINO.

### Verso la prossima lezione

Ora sappiamo trasformare frequenze in lunghezze di codice. La domanda successiva è come stimare probabilità e valutarle.
