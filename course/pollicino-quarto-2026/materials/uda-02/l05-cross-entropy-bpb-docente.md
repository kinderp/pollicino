# POLLICINO — UDA 2, Lezione 05 — materiale docente
## Cross-entropy e bits-per-byte come metrica comune

### Funzione della lezione nel percorso

**Focus docente:** Questa è la cerniera matematica del corso: non procedere se non è chiaro che previsione e compressione condividono lo stesso costo logaritmico.

La domanda guida per la classe è: **Come confrontiamo RLE, frequenze, n-gram e futuri modelli neurali usando la stessa unità di misura?**  
Questa lezione appartiene a `uda-02-compressione-predizione` e deve restare sincronizzata con l'handout studenti omonimo.

### Nucleo concettuale

La cross-entropy empirica è `H(p,q) = E_p[-log2 q(X)]`. Per un modello sequenziale si usa la probabilità condizionata del token corretto a ogni passo. Con logaritmo naturale, la loss in nat si converte in bit dividendo per `ln 2`. La perplessità è `2^bpb` quando l'unità è il byte e la loss è espressa in bit.

### Lettura scientifica

Tutte le curve di training POLLICINO dovrebbero riportare NLL e bpb su validation/test, oltre alla dimensione reale del codec.

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

La cross-entropy empirica è `H(p,q) = E_p[-log2 q(X)]`. Per un modello sequenziale si usa la probabilità condizionata del token corretto a ogni passo. Con logaritmo naturale, la loss in nat si converte in bit dividendo per `ln 2`. La perplessità è `2^bpb` quando l'unità è il byte e la loss è espressa in bit.

### Strategia di lezione suggerita

1. Partire dalla domanda guida e da un esempio piccolo che si possa calcolare alla lavagna.
2. Fare formulare una previsione agli studenti **prima** dell'esperimento.
3. Eseguire o simulare il micro-esperimento: Implementa una funzione che riceve le probabilità assegnate ai byte corretti e calcola NLL in bit e bpb. Confronta uniforme, distribuzione zero-order e bigramma sullo stesso split di test. Salva i risultati in una tabella riproducibile.
4. Separare osservazione e interpretazione: prima i numeri, poi la spiegazione.
5. Chiudere collegando il risultato alla metrica comune del corso o al round-trip lossless.

### Misconcezioni previste

- **Bpb è già la dimensione esatta del file compresso**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Perplexity e bpb sono intercambiabili senza specificare base e tokenizzazione**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Una loss di training è sufficiente per giudicare il codec**: chiedere agli studenti un controesempio prima di correggere formalmente.

### Soluzioni / criteri attesi per gli esercizi

Le risposte non devono essere identiche nel testo, ma dovrebbero mostrare:
- distinzione tra dato osservato e conclusione generale;
- consapevolezza dell'overhead o dei vincoli computazionali;
- capacità di collegare il concetto alla previsione del prossimo byte;
- quando pertinente, distinzione tra **costo ideale** del modello e **dimensione reale** del codec;
- quando pertinente, uso corretto di train/validation/test.

### Ponte verso PyTorch / MLX / codec

UDA 3 sostituisce le tabelle sparse con funzioni parametrizzate che imparano da esempi.

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
- Documentazione concettuale su negative log-likelihood e cross-entropy.

> Nota editoriale: i riferimenti sono una base di lavoro. Durante il corso possiamo aggiungere pagine, figure, esercizi e fonti più mirate senza cambiare l'ID della lezione.
