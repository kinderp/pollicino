# POLLICINO — UDA 6, Lezione 01
## Dal modello probabilistico al range coder

**Domanda guida:** se il modello assegna probabilità al prossimo byte, come trasformiamo quella probabilità in bit reali?

### Teoria
La cross-entropy ci dice il costo ideale di una sequenza, ma non produce un file compresso. Un **entropy coder** usa le probabilità per costruire un bitstream. Arithmetic coding e range coding rappresentano progressivamente la sequenza dentro intervalli: eventi probabili occupano intervalli più grandi e quindi costano meno informazione.

L'idea chiave è che la lunghezza dell'intervallo finale è collegata al prodotto delle probabilità assegnate ai simboli. Da qui riappare il costo `-log2(p)` studiato nelle prime UDA.

### Esempio
Con un alfabeto di due simboli, se A ha probabilità 0,75 e B 0,25, l'intervallo di A è più grande. Dopo ogni simbolo scegliamo il sottointervallo corrispondente e continuiamo.

### Micro-esperimento
Simula arithmetic coding su 2–4 simboli usando frazioni o alta precisione. Disegna gli intervalli dopo ogni simbolo. Solo dopo passa a frequenze cumulative intere e range coding.

### Da ricordare
- il coder non migliora un modello probabilistico cattivo;
- cross-entropy e bitstream sono due livelli diversi;
- encoder e decoder devono usare esattamente le stesse distribuzioni discrete.

### Ponte
La prossima lezione affronta il problema più delicato: mantenere encoder e decoder perfettamente sincronizzati.
