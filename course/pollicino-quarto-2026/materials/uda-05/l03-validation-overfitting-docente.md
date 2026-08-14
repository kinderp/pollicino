# UDA 5 — L03 — materiale docente
## Generalizzazione e model selection

### Concetti
Training aggiorna i pesi; validation guida model selection; test stima finale. Consultare ripetutamente il test introduce selection bias.

### Didattica
Usare curve reali del progetto. Chiedere agli studenti di diagnosticare: underfitting, apprendimento sano, overfitting, instabilità. È più efficace di definizioni isolate.

### Early stopping
Può essere presentato come scelta del checkpoint basata su validation, non come garanzia teorica. Riportare best step e criterio usato.

### Collegamento a POLLICINO
Le ablation dell'UDA 6 devono essere decise su validation; il test corpus finale deve restare congelato. Per confronti più forti considerare più seed o almeno discutere la varianza.

### Errore da evitare
“Loss più bassa” senza specificare split, tokenizzazione/unità e dataset non è un risultato confrontabile.
