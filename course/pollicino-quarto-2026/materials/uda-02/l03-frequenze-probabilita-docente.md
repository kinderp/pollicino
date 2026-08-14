# POLLICINO — UDA 2, Lezione 03 — materiale docente
## Dalle frequenze alle probabilità empiriche

### Funzione della lezione nel percorso

**Focus docente:** Collegare statistica descrittiva e generalizzazione: train e test possono avere distribuzioni differenti.

La domanda guida per la classe è: **Come trasformiamo ciò che abbiamo osservato in una previsione sul prossimo byte?**  
Questa lezione appartiene a `uda-02-compressione-predizione` e deve restare sincronizzata con l'handout studenti omonimo.

### Nucleo concettuale

La stima di massima verosimiglianza per una multinomiale usa `p_hat_i = n_i / N`. Gli eventi mai osservati ricevono probabilità zero, problema grave se poi compaiono nel test. È sufficiente introdurre intuitivamente smoothing/pseudocount senza ancora sviluppare Bayesian inference.

### Lettura scientifica

Le distribuzioni empiriche diventano la baseline zero-order contro cui misurare n-gram e Transformer.

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

La stima di massima verosimiglianza per una multinomiale usa `p_hat_i = n_i / N`. Gli eventi mai osservati ricevono probabilità zero, problema grave se poi compaiono nel test. È sufficiente introdurre intuitivamente smoothing/pseudocount senza ancora sviluppare Bayesian inference.

### Strategia di lezione suggerita

1. Partire dalla domanda guida e da un esempio piccolo che si possa calcolare alla lavagna.
2. Fare formulare una previsione agli studenti **prima** dell'esperimento.
3. Eseguire o simulare il micro-esperimento: Conta i 256 byte su almeno quattro categorie di file. Stampa i dieci byte più frequenti, la frequenza relativa e l'entropia zero-order. Confronta i grafici o una tabella e annota quali categorie sembrano più prevedibili senza contesto.
4. Separare osservazione e interpretazione: prima i numeri, poi la spiegazione.
5. Chiudere collegando il risultato alla metrica comune del corso o al round-trip lossless.

### Misconcezioni previste

- **Frequenza osservata e probabilità vera sono la stessa cosa**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Un byte non osservato è impossibile**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **L'istogramma conserva l'ordine dei byte**: chiedere agli studenti un controesempio prima di correggere formalmente.

### Soluzioni / criteri attesi per gli esercizi

Le risposte non devono essere identiche nel testo, ma dovrebbero mostrare:
- distinzione tra dato osservato e conclusione generale;
- consapevolezza dell'overhead o dei vincoli computazionali;
- capacità di collegare il concetto alla previsione del prossimo byte;
- quando pertinente, distinzione tra **costo ideale** del modello e **dimensione reale** del codec;
- quando pertinente, uso corretto di train/validation/test.

### Ponte verso PyTorch / MLX / codec

L'istogramma ignora l'ordine. Nella prossima lezione useremo il contesto per fare previsioni diverse a seconda dei byte precedenti.

Quando la lezione viene implementata con un framework, conviene mantenere prima un caso minuscolo controllabile a mano o con Python puro. Il framework deve sostituire lavoro meccanico, non il significato del concetto.

### Evidenze da conservare nel repository

- configurazione dell'esperimento;
- input o manifest del corpus;
- metriche principali;
- eventuali seed/versioni/backend;
- test di round-trip se è presente codifica lossless;
- una breve nota su risultati inattesi o negativi.

### Riferimenti per l'affinamento

- Cover & Thomas, Elements of Information Theory
- Qualunque testo introduttivo su stima multinomiale e smoothing additivo.

> Nota editoriale: i riferimenti sono una base di lavoro. Durante il corso possiamo aggiungere pagine, figure, esercizi e fonti più mirate senza cambiare l'ID della lezione.
