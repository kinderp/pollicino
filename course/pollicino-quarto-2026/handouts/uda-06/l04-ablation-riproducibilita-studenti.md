# POLLICINO — UDA 6, Lezione 04
## Ablation, controlli e riproducibilità scientifica

**Domanda guida:** se una nuova versione migliora, come scopriamo quale modifica ha davvero causato il miglioramento?

### Teoria
Un'**ablation** cambia una componente alla volta mantenendo il resto il più possibile fisso. Se aumentiamo insieme context length, profondità, dataset e training budget, possiamo osservare un guadagno ma non sappiamo quale cambiamento lo abbia prodotto.

Prima di eseguire una run scriviamo l'ipotesi e la metrica primaria. Dopo la run conserviamo anche i risultati negativi: possono dimostrare che un'idea non porta vantaggi nelle condizioni provate.

### Variabili possibili
- context length;
- numero di layer o heads;
- width/embedding size;
- n-gram vs MLP vs Transformer;
- precisione della CDF;
- budget di training.

### Provenienza minima
Commit, configurazione, dataset manifest, seed, ambiente/backend, log e output.

### Micro-esperimento
Progetta una matrice di 3–5 ablation. Scrivi prima cosa ti aspetti e perché. Poi esegui o simula il protocollo e confronta validation bpb e costo.

### Ponte
L'ultima lezione trasforma il percorso in una challenge con report tecnico completo.
