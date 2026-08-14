# POLLICINO — UDA 2, Lezione 01
## Ridondanza e Run-Length Encoding

**Domanda guida:** Quando una sequenza ripete spesso lo stesso simbolo, possiamo descriverla con meno simboli?

### Obiettivi
- Comprendere il concetto centrale della lezione e collegarlo alla compressione lossless.
- Saper leggere o costruire un piccolo esempio numerico o di codice.
- Saper spiegare che cosa misura l'esperimento e quali conclusioni sono lecite.

### Perché ci serve in POLLICINO

Dalle ridondanze visibili ai modelli probabilistici di contesto. In questa lezione lavoriamo su **Ridondanza e Run-Length Encoding**. Il criterio resta sempre lo stesso: ogni nuova idea deve aiutarci a descrivere i byte in modo più corto senza perdere la possibilità di ricostruirli esattamente.

### Idea fondamentale

La compressione lossless cerca una descrizione più corta che permetta di ricostruire esattamente i dati originali. Il caso più semplice è una sequenza con lunghe ripetizioni: invece di scrivere `AAAAAA`, possiamo descriverla come “6 volte A”. Questa idea è il Run-Length Encoding (RLE). RLE non è una magia universale: funziona bene solo quando i run sono abbastanza lunghi da compensare il costo con cui memorizziamo simbolo e conteggio.

### Esempio ragionato

Confronta `AAAAAAAAAABBBCC` con `ABACADAEAF`. Nel primo caso esistono run lunghi; nel secondo quasi nessuno. Una codifica RLE del tipo `(conteggio, simbolo)` può ridurre molto il primo file e perfino ingrandire il secondo. Per questo un compressore serio deve misurare il guadagno invece di presumere che una tecnica sia sempre conveniente.

### Esperimento guidato

Scrivi una funzione che riceve una sequenza di byte o una stringa e restituisce le coppie `(conteggio, simbolo)`. Aggiungi poi il decoder e verifica automaticamente `decode(encode(x)) == x` su casi normali, file vuoti e run molto lunghi. Misura dimensione originale e dimensione codificata.

Durante l'esperimento conserva almeno input, configurazione e risultato. Se produci un encoder o un decoder, il controllo più importante è il **round-trip**: ciò che decodifichi deve essere identico, byte per byte, all'originale.

### Che cosa osservare

Non limitarti a dire “funziona” o “non funziona”. Chiediti:
- quale informazione usa il metodo;
- quale costo introduce;
- su quali dati sembra funzionare meglio;
- se il risultato vale sul training, sul test o su entrambi;
- come cambierebbe il risultato usando un contesto o un modello diverso.

### Errori da evitare

- compressione significa sempre file più piccolo.
- lossless permette di cambiare qualche byte.
- un algoritmo efficace su un dataset è automaticamente efficace su tutti.

### Esercizi

1. Spiega con parole tue la risposta alla domanda guida: **Quando una sequenza ripete spesso lo stesso simbolo, possiamo descriverla con meno simboli?**
2. Individua un caso in cui l'idea della lezione potrebbe fallire o essere poco utile.
3. Collega il concetto a una delle metriche già usate in POLLICINO: dimensione, probabilità, loss o bits-per-byte.

### Exit ticket

In massimo cinque righe scrivi:
1. qual è l'input del metodo visto oggi;
2. qual è il suo output;
3. quale misura useresti per capire se è utile a POLLICINO.

### Verso la prossima lezione

RLE usa una regola molto specifica. La prossima lezione generalizza l'idea: dare codici corti ai simboli frequenti.
