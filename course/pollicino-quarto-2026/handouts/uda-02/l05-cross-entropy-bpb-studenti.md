# POLLICINO — UDA 2, Lezione 05
## Cross-entropy e bits-per-byte come metrica comune

**Domanda guida:** Come confrontiamo RLE, frequenze, n-gram e futuri modelli neurali usando la stessa unità di misura?

### Obiettivi
- Comprendere il concetto centrale della lezione e collegarlo alla compressione lossless.
- Saper leggere o costruire un piccolo esempio numerico o di codice.
- Saper spiegare che cosa misura l'esperimento e quali conclusioni sono lecite.

### Perché ci serve in POLLICINO

Dalle ridondanze visibili ai modelli probabilistici di contesto. In questa lezione lavoriamo su **Cross-entropy e bits-per-byte come metrica comune**. Il criterio resta sempre lo stesso: ogni nuova idea deve aiutarci a descrivere i byte in modo più corto senza perdere la possibilità di ricostruirli esattamente.

### Idea fondamentale

Se un modello assegna probabilità alta al simbolo corretto, quel simbolo costa pochi bit ideali; se gli assegna probabilità bassa, costa molti bit. Sommando `-log2(p)` per tutti i byte e dividendo per il numero di byte otteniamo i bits per byte (bpb). È una metrica indipendente dal fatto che il modello sia una semplice tabella o un Transformer.

### Esempio ragionato

La baseline uniforme assegna 1/256 a ogni byte e costa esattamente 8 bpb. Se un modello ottiene 5 bpb sullo stesso test, significa che le sue probabilità contengono abbastanza informazione per descrivere idealmente il file con circa 5 bit per byte, prima di considerare overhead e imperfezioni del coder.

### Esperimento guidato

Implementa una funzione che riceve le probabilità assegnate ai byte corretti e calcola NLL in bit e bpb. Confronta uniforme, distribuzione zero-order e bigramma sullo stesso split di test. Salva i risultati in una tabella riproducibile.

Durante l'esperimento conserva almeno input, configurazione e risultato. Se produci un encoder o un decoder, il controllo più importante è il **round-trip**: ciò che decodifichi deve essere identico, byte per byte, all'originale.

### Che cosa osservare

Non limitarti a dire “funziona” o “non funziona”. Chiediti:
- quale informazione usa il metodo;
- quale costo introduce;
- su quali dati sembra funzionare meglio;
- se il risultato vale sul training, sul test o su entrambi;
- come cambierebbe il risultato usando un contesto o un modello diverso.

### Errori da evitare

- bpb è già la dimensione esatta del file compresso.
- perplexity e bpb sono intercambiabili senza specificare base e tokenizzazione.
- una loss di training è sufficiente per giudicare il codec.

### Esercizi

1. Spiega con parole tue la risposta alla domanda guida: **Come confrontiamo RLE, frequenze, n-gram e futuri modelli neurali usando la stessa unità di misura?**
2. Individua un caso in cui l'idea della lezione potrebbe fallire o essere poco utile.
3. Collega il concetto a una delle metriche già usate in POLLICINO: dimensione, probabilità, loss o bits-per-byte.

### Exit ticket

In massimo cinque righe scrivi:
1. qual è l'input del metodo visto oggi;
2. qual è il suo output;
3. quale misura useresti per capire se è utile a POLLICINO.

### Verso la prossima lezione

UDA 3 sostituisce le tabelle sparse con funzioni parametrizzate che imparano da esempi.
