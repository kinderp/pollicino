# POLLICINO — UDA 5, Lezione 02
## Reference implementation e training loop in PyTorch

### Il ciclo minimo
Un training step contiene una sequenza precisa:
1. prendi un batch;
2. calcola logits e loss;
3. azzera i gradienti precedenti;
4. esegui backpropagation;
5. fai lo step dell'optimizer;
6. registra metriche.

Ogni passaggio deve essere osservabile. Se la loss non scende dobbiamo poter distinguere problemi nei dati, nel forward, nella loss, nei gradienti o nell'optimizer.

### Primo obiettivo
Non cerchiamo subito il miglior bpb. Prima vogliamo una pipeline che riesca a overfittare un corpus minuscolo, salvare un checkpoint, ricaricarlo e produrre di nuovo output coerenti.

### Micro-esperimento
Implementa il loop del tiny Transformer in PyTorch. Registra train loss, validation loss e bpb. Salva configurazione e checkpoint; ricaricali in un nuovo processo.

### Da ricordare
- `backward()` calcola gradienti, non aggiorna da solo i pesi;
- un checkpoint utile comprende almeno pesi e configurazione, e spesso stato optimizer;
- stesso seed non garantisce necessariamente bitwise-identical training su ogni hardware.

### Ponte
La prossima lezione ci insegna a scegliere il checkpoint senza confondere apprendimento e memorizzazione.
