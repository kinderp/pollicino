# POLLICINO — UDA 6, Lezione 05
## POLLICINO Challenge: dal prototipo al report di ricerca

### Sfida finale
La challenge non premia soltanto il file più piccolo. Un progetto completo deve dimostrare:
- round-trip lossless;
- baseline dichiarate;
- corpus e split identificabili;
- configurazione riproducibile;
- metriche di qualità e costo;
- analisi dei limiti;
- conclusioni proporzionate alle evidenze.

### Protocollo
Congela un corpus finale. Esegui il sistema con una configurazione versionata. Conserva hash degli input, log, output, tabella risultati e test di decodifica. Scrivi poi una relazione breve con **ipotesi, metodo, risultati, limiti e prossimi esperimenti**.

### Un buon risultato
“Su questo corpus, con questo commit e questa configurazione, il modello A riduce il bpb reale da X a Y rispetto alla baseline, con questi costi e questi casi in cui fallisce.”

### Un risultato da evitare
“Abbiamo creato il miglior compressore” senza corpus, protocollo o confronto sufficiente.

### Anche un risultato negativo vale
Se un'idea non migliora il codec ma l'esperimento è corretto e riproducibile, abbiamo imparato qualcosa di utile.

### Chiusura
Ripercorri l'anno: byte → informazione → probabilità → n-gram → rete neurale → attention → Transformer → cross-entropy → range coder → codec lossless. Il filo conduttore non era “usare l'AI”, ma capire come una previsione migliore possa diventare una descrizione più corta.
