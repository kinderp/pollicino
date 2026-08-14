# POLLICINO — UDA 2, Lezione 04 — materiale docente
## Contesto, n-gram e modelli di Markov

### Funzione della lezione nel percorso

**Focus docente:** Usare train/test split già qui. È il momento giusto per far vedere overfitting senza chiamarlo ancora deep learning.

La domanda guida per la classe è: **Il prossimo byte dipende soltanto da quanto è frequente in generale, o anche da ciò che lo precede?**  
Questa lezione appartiene a `uda-02-compressione-predizione` e deve restare sincronizzata con l'handout studenti omonimo.

### Nucleo concettuale

Un modello Markov di ordine k approssima `P(x_t | x_<t)` con `P(x_t | x_{t-k:t})`. Il numero potenziale di contesti cresce come `256^k`; la sparsità rende impraticabile una tabella densa per k elevati. Qui nasce il problema che le reti neurali cercheranno di risolvere condividendo parametri tra contesti simili.

### Lettura scientifica

La funzione obiettivo del Transformer sarà la stessa del modello n-gram: prevedere il prossimo byte minimizzando NLL.

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

Un modello Markov di ordine k approssima `P(x_t | x_<t)` con `P(x_t | x_{t-k:t})`. Il numero potenziale di contesti cresce come `256^k`; la sparsità rende impraticabile una tabella densa per k elevati. Qui nasce il problema che le reti neurali cercheranno di risolvere condividendo parametri tra contesti simili.

### Strategia di lezione suggerita

1. Partire dalla domanda guida e da un esempio piccolo che si possa calcolare alla lavagna.
2. Fare formulare una previsione agli studenti **prima** dell'esperimento.
3. Eseguire o simulare il micro-esperimento: Costruisci un contatore bigramma 256x256. Per ogni byte precedente, stima la distribuzione del successivo con smoothing. Calcola la cross-entropy sul file di test. Se vuoi estendere, prova trigrammi con un dizionario sparso e confronta memoria e qualità.
4. Separare osservazione e interpretazione: prima i numeri, poi la spiegazione.
5. Chiudere collegando il risultato alla metrica comune del corso o al round-trip lossless.

### Misconcezioni previste

- **Più n significa sempre modello migliore**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Un n-gram comprende il significato**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Un modello con loss più bassa sul training generalizza automaticamente**: chiedere agli studenti un controesempio prima di correggere formalmente.

### Soluzioni / criteri attesi per gli esercizi

Le risposte non devono essere identiche nel testo, ma dovrebbero mostrare:
- distinzione tra dato osservato e conclusione generale;
- consapevolezza dell'overhead o dei vincoli computazionali;
- capacità di collegare il concetto alla previsione del prossimo byte;
- quando pertinente, distinzione tra **costo ideale** del modello e **dimensione reale** del codec;
- quando pertinente, uso corretto di train/validation/test.

### Ponte verso PyTorch / MLX / codec

Abbiamo un vero predittore. Ora possiamo confrontare tutti i modelli con una misura unica: cross-entropy in bit per byte.

Quando la lezione viene implementata con un framework, conviene mantenere prima un caso minuscolo controllabile a mano o con Python puro. Il framework deve sostituire lavoro meccanico, non il significato del concetto.

### Evidenze da conservare nel repository

- configurazione dell'esperimento;
- input o manifest del corpus;
- metriche principali;
- eventuali seed/versioni/backend;
- test di round-trip se è presente codifica lossless;
- una breve nota su risultati inattesi o negativi.

### Riferimenti per l'affinamento

- Claude Shannon, A Mathematical Theory of Communication, 1948
- Testi introduttivi su Markov chains e language models n-gram.

> Nota editoriale: i riferimenti sono una base di lavoro. Durante il corso possiamo aggiungere pagine, figure, esercizi e fonti più mirate senza cambiare l'ID della lezione.
