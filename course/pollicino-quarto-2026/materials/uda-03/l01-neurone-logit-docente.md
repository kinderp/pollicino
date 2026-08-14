# UDA 3 — L01 — materiale docente
## Dal punteggio al logit

### Nucleo scientifico
Una trasformazione affine `z = Wx + b` è il primo modello parametrico del corso. Conviene evitare di attribuirle proprietà “intelligenti”: il punto didattico è mostrare che i valori di `W` e `b` possono essere appresi minimizzando una funzione obiettivo.

Nel byte model finale la proiezione di output produrrà un vettore di 256 logits. Il logit ha significato solo **relativo** agli altri logits e verrà normalizzato da softmax.

### Strategia
1. partire da una funzione con due input;
2. far modificare i pesi a mano;
3. estendere da scalare a vettore;
4. collegare l'output ai 256 possibili byte.

### Errori tipici
- confondere logit e probabilità;
- pensare che il valore numerico del byte sia già una buona caratteristica continua;
- presentare il neurone artificiale come copia fedele del neurone biologico.

### Collegamento a POLLICINO
Il Transformer terminerà con una proiezione lineare verso 256 logits. Questa lezione prepara quindi esattamente l'ultimo stadio del modello, prima della cross-entropy.

### Risultato atteso
Lo studente deve saper leggere `z = Wx+b`, spiegare che i parametri sono appresi e distinguere il punteggio dalla probabilità.

**Riferimento di approfondimento:** Goodfellow, Bengio, Courville, *Deep Learning*, capitoli introduttivi.
