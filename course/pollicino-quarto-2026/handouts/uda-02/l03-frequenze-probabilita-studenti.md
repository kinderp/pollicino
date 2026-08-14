# POLLICINO — UDA 2, Lezione 03
## Dalle frequenze alle probabilità empiriche

**Domanda guida:** Come trasformiamo ciò che abbiamo osservato in una previsione sul prossimo byte?

### Obiettivi
- Comprendere il concetto centrale della lezione e collegarlo alla compressione lossless.
- Saper leggere o costruire un piccolo esempio numerico o di codice.
- Saper spiegare che cosa misura l'esperimento e quali conclusioni sono lecite.

### Perché ci serve in POLLICINO

Dalle ridondanze visibili ai modelli probabilistici di contesto. In questa lezione lavoriamo su **Dalle frequenze alle probabilità empiriche**. Il criterio resta sempre lo stesso: ogni nuova idea deve aiutarci a descrivere i byte in modo più corto senza perdere la possibilità di ricostruirli esattamente.

### Idea fondamentale

Se in un file il byte `0x20` compare 1800 volte su 10000, una prima stima della sua probabilità è 0,18. Questa probabilità empirica non è una legge universale: descrive il campione osservato. Cambiando tipo di file, lingua o formato, cambiano le frequenze. Un modello di compressione usa queste stime per assegnare più probabilità agli eventi che si aspetta.

### Esempio ragionato

Due file della stessa dimensione possono avere istogrammi completamente diversi. Un testo ASCII tende a concentrare massa su un sottoinsieme di byte; un file cifrato o già compresso può apparire quasi uniforme. L'istogramma è quindi una prima “impronta statistica” del contenuto.

### Esperimento guidato

Conta i 256 byte su almeno quattro categorie di file. Stampa i dieci byte più frequenti, la frequenza relativa e l'entropia zero-order. Confronta i grafici o una tabella e annota quali categorie sembrano più prevedibili senza contesto.

Durante l'esperimento conserva almeno input, configurazione e risultato. Se produci un encoder o un decoder, il controllo più importante è il **round-trip**: ciò che decodifichi deve essere identico, byte per byte, all'originale.

### Che cosa osservare

Non limitarti a dire “funziona” o “non funziona”. Chiediti:
- quale informazione usa il metodo;
- quale costo introduce;
- su quali dati sembra funzionare meglio;
- se il risultato vale sul training, sul test o su entrambi;
- come cambierebbe il risultato usando un contesto o un modello diverso.

### Errori da evitare

- frequenza osservata e probabilità vera sono la stessa cosa.
- un byte non osservato è impossibile.
- l'istogramma conserva l'ordine dei byte.

### Esercizi

1. Spiega con parole tue la risposta alla domanda guida: **Come trasformiamo ciò che abbiamo osservato in una previsione sul prossimo byte?**
2. Individua un caso in cui l'idea della lezione potrebbe fallire o essere poco utile.
3. Collega il concetto a una delle metriche già usate in POLLICINO: dimensione, probabilità, loss o bits-per-byte.

### Exit ticket

In massimo cinque righe scrivi:
1. qual è l'input del metodo visto oggi;
2. qual è il suo output;
3. quale misura useresti per capire se è utile a POLLICINO.

### Verso la prossima lezione

L'istogramma ignora l'ordine. Nella prossima lezione useremo il contesto per fare previsioni diverse a seconda dei byte precedenti.
