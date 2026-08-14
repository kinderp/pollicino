# POLLICINO — UDA 4, Lezione 04
## Multi-head attention, residual, normalization e feed-forward

### Idea fondamentale
Un blocco Transformer non contiene solo una testa di attention. Usa più teste, connessioni residuali, normalizzazione e una rete feed-forward. Ogni componente risolve un problema diverso.

Le **multi-head** applicano più proiezioni Q/K/V; gli output vengono concatenati e riproiettati. Le **residual** mantengono un percorso diretto dell'informazione. La **normalization** stabilizza le scale. La **feed-forward network** applica una trasformazione non lineare indipendente a ogni posizione.

### Una variante di riferimento
Per POLLICINO useremo come prima versione una struttura pre-norm concettuale:
`x = x + Attention(Norm(x))`
`x = x + MLP(Norm(x))`.
Esistono altre varianti: per questo architettura e configurazione devono essere registrate negli esperimenti.

### Micro-esperimento
Costruisci un blocco che riceve `(B,T,C)` e restituisce la stessa shape. Conta i parametri. Prova un forward su input casuali e verifica che le residual non cambino la dimensione.

### Errori da evitare
- una testa non corrisponde necessariamente a un concetto umano;
- normalization non è compressione;
- residual non rende il training automaticamente corretto.

### Ponte
Nella prossima lezione impileremo i blocchi e costruiremo il tiny Transformer completo.
