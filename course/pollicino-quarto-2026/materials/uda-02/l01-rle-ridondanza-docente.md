# POLLICINO — UDA 2, Lezione 01 — materiale docente
## Ridondanza e Run-Length Encoding

### Funzione della lezione nel percorso

**Focus docente:** Usare RLE per fissare tre invarianti: reversibilità, misurazione del costo reale e separazione tra modello e formato.

La domanda guida per la classe è: **Quando una sequenza ripete spesso lo stesso simbolo, possiamo descriverla con meno simboli?**  
Questa lezione appartiene a `uda-02-compressione-predizione` e deve restare sincronizzata con l'handout studenti omonimo.

### Nucleo concettuale

RLE sfrutta una forma elementare di ridondanza locale. Se un run di lunghezza r viene rappresentato con c byte di overhead più il simbolo, la sostituzione conviene solo quando r supera il costo della rappresentazione. È utile introdurre già qui il rapporto `compressed_size / original_size` e distinguere ratio, saving percentuale e overhead di formato.

### Lettura scientifica

POLLICINO dovrà sempre battere baseline semplici includendo header e metadati, non solo il payload ideale.

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

RLE sfrutta una forma elementare di ridondanza locale. Se un run di lunghezza r viene rappresentato con c byte di overhead più il simbolo, la sostituzione conviene solo quando r supera il costo della rappresentazione. È utile introdurre già qui il rapporto `compressed_size / original_size` e distinguere ratio, saving percentuale e overhead di formato.

### Strategia di lezione suggerita

1. Partire dalla domanda guida e da un esempio piccolo che si possa calcolare alla lavagna.
2. Fare formulare una previsione agli studenti **prima** dell'esperimento.
3. Eseguire o simulare il micro-esperimento: Scrivi una funzione che riceve una sequenza di byte o una stringa e restituisce le coppie `(conteggio, simbolo)`. Aggiungi poi il decoder e verifica automaticamente `decode(encode(x)) == x` su casi normali, file vuoti e run molto lunghi. Misura dimensione originale e dimensione codificata.
4. Separare osservazione e interpretazione: prima i numeri, poi la spiegazione.
5. Chiudere collegando il risultato alla metrica comune del corso o al round-trip lossless.

### Misconcezioni previste

- **Compressione significa sempre file più piccolo**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Lossless permette di cambiare qualche byte**: chiedere agli studenti un controesempio prima di correggere formalmente.
- **Un algoritmo efficace su un dataset è automaticamente efficace su tutti**: chiedere agli studenti un controesempio prima di correggere formalmente.

### Soluzioni / criteri attesi per gli esercizi

Le risposte non devono essere identiche nel testo, ma dovrebbero mostrare:
- distinzione tra dato osservato e conclusione generale;
- consapevolezza dell'overhead o dei vincoli computazionali;
- capacità di collegare il concetto alla previsione del prossimo byte;
- quando pertinente, distinzione tra **costo ideale** del modello e **dimensione reale** del codec;
- quando pertinente, uso corretto di train/validation/test.

### Ponte verso PyTorch / MLX / codec

RLE usa una regola molto specifica. La prossima lezione generalizza l'idea: dare codici corti ai simboli frequenti.

Quando la lezione viene implementata con un framework, conviene mantenere prima un caso minuscolo controllabile a mano o con Python puro. Il framework deve sostituire lavoro meccanico, non il significato del concetto.

### Evidenze da conservare nel repository

- configurazione dell'esperimento;
- input o manifest del corpus;
- metriche principali;
- eventuali seed/versioni/backend;
- test di round-trip se è presente codifica lossless;
- una breve nota su risultati inattesi o negativi.

### Riferimenti per l'affinamento

- David Salomon, Data Compression: The Complete Reference
- RFC e formati reali possono essere mostrati solo come esempi, senza trasformare RLE in una lezione di standard.

> Nota editoriale: i riferimenti sono una base di lavoro. Durante il corso possiamo aggiungere pagine, figure, esercizi e fonti più mirate senza cambiare l'ID della lezione.
