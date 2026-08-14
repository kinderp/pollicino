# POLLICINO — UDA 2, Lezione 02 — materiale docente
## Huffman e codici a prefisso

### Funzione della lezione nel percorso

**Focus docente:** Far distinguere nettamente modello di probabilità e codificatore: Huffman contiene entrambi solo nel caso statico più semplice.

La domanda guida per la classe è: **Se alcuni simboli compaiono più spesso, perché dovrebbero occupare lo stesso numero di bit degli altri?**  
Questa lezione appartiene a `uda-02-compressione-predizione` e deve restare sincronizzata con l'handout studenti omonimo.

### Nucleo concettuale

Huffman produce un codice prefisso ottimo tra i codici simbolo-per-simbolo a lunghezza intera per una distribuzione nota. La lunghezza media è vicina all'entropia ma non può usare frazioni di bit per singolo simbolo. Questo prepara il bisogno di codificatori aritmetici/range, che possono avvicinarsi meglio a `-log2 p` su sequenze.

### Lettura scientifica

Nel codec neurale di POLLICINO il Transformer produrrà probabilità; un entropy coder separato convertirà quelle probabilità in bit.

L'obiettivo non è anticipare tutto il formalismo universitario, ma fare in modo che la semplificazione usata in classe sia compatibile con l'oggetto matematico e computazionale che useremo nella ricerca. Quando un passaggio viene omesso, va presentato come **semplificazione didattica**, non come proprietà generale.

### Derivazione / notazione da mantenere

La notazione deve restare coerente lungo tutto il corso:
- `x_t` indica il byte osservato alla posizione `t`;
- `x_<t` indica il contesto precedente;
- `q_theta(x_t | x_<t)` indica la probabilità assegnata dal modello;
- la loss di previsione è una negative log-likelihood;
- quando usiamo logaritmi in base 2, il costo è direttamente espresso in bit;
- `bpb` significa **bits per byte** sul dataset dichiarato.

Per questa lezione la formalizzazione specifica è:

Huffman produce un codice prefisso ottimo tra i codici simbolo-per-simbolo a lunghezza intera per una distribuzione nota. La lunghezza media è vicina all'entropia ma non può usare frazioni di bit per singolo simbolo. Questo prepara il bisogno di codificatori aritmetici/range, che possono avvicinarsi meglio a `-log2 p` su sequenze.

### Strategia di lezione suggerita

1. Partire dalla domanda guida e da un esempio piccolo che si possa calcolare alla lavagna.
2. Fare formulare una previsione agli studenti **prima** dell'esperimento.
3. Eseguire o simulare il micro-esperimento: Calcola le frequenze dei byte di un piccolo file, costruisci l'albero combinando ogni volta i due nodi meno frequenti, genera la tabella dei codici e misura il numero totale di bit teorici. Se implementi encoder e decoder, aggiungi la verifica round-trip.
4. Separare osservazione e interpretazione: prima i numeri, poi la spiegazione.
5. Chiudere collegando il risultato alla metrica comune del corso o al round-trip lossless.

### Misconcezioni previste

- **Il simbolo più frequente ha sempre codice 0**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **L'albero di huffman è unico**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Huffman usa il contesto precedente**: chiedere agli studenti un controesempio prima di correggere formalmente.

### Soluzioni / criteri attesi per gli esercizi

Le risposte non devono essere identiche nel testo, ma dovrebbero mostrare:
- distinzione tra dato osservato e conclusione generale;
- consapevolezza dell'overhead o dei vincoli computazionali;
- capacità di collegare il concetto alla previsione del prossimo byte;
- quando pertinente, distinzione tra **costo ideale** del modello e **dimensione reale** del codec;
- quando pertinente, uso corretto di train/validation/test.

### Ponte verso PyTorch / MLX / codec

Ora sappiamo trasformare frequenze in lunghezze di codice. La domanda successiva è come stimare probabilità e valutarle.

Quando la lezione viene implementata con un framework, conviene mantenere prima un caso minuscolo controllabile a mano o con Python puro. Il framework deve sostituire lavoro meccanico, non il significato del concetto.

### Evidenze da conservare nel repository

- configurazione dell'esperimento;
- input o manifest del corpus;
- metriche principali;
- eventuali seed/versioni/backend;
- test di round-trip se è presente codifica lossless;
- una breve nota su risultati inattesi o negativi.

### Riferimenti per l'affinamento

- D. A. Huffman, A Method for the Construction of Minimum-Redundancy Codes, 1952
- Cover & Thomas, Elements of Information Theory

> Nota editoriale: i riferimenti sono una base di lavoro. Durante il corso possiamo aggiungere pagine, figure, esercizi e fonti più mirate senza cambiare l'ID della lezione.
