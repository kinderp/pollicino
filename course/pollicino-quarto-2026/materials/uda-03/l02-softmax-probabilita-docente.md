# UDA 3 — L02 — materiale docente
## Softmax

### Formalizzazione
`softmax(z)_i = exp(z_i) / Σ_j exp(z_j)`. L'invarianza per traslazione permette la forma stabile `softmax(z-max(z))`. È utile collegare questo passaggio al log-sum-exp che apparirà implicitamente nelle implementazioni stabili della cross-entropy.

### Obiettivo didattico
Far vedere il collegamento diretto tra output della rete e probabilità necessarie al codec. L'uguaglianza di tutti i logits deve essere usata per ritrovare la distribuzione uniforme e gli 8 bpb: è un ponte importante con UDA 1 e 2.

### Misconcezioni
- softmax come argmax;
- interpretazione assoluta dei logits;
- stabilizzazione numerica vista come dettaglio opzionale.

### Attività
Usare vettori di 3 elementi calcolabili a mano; solo dopo passare a 256. Far provocare overflow con valori grandi e spiegare perché la formula stabile è necessaria.

### Collegamento scientifico
Nell'implementazione reale preferiremo primitive di loss stabili del backend anziché calcolare `softmax` e poi `log` separatamente quando non serve. Il significato matematico, però, resta quello studiato qui.
