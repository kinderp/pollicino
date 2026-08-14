# UDA 6 — L02 — materiale docente
## Determinismo del codec

### Invariante
`D(E(x)) = x`. Questo test deve precedere qualsiasi claim di compressione.

### Pipeline
Encoder: prefisso -> modello -> logits -> CDF deterministica -> range encoder. Decoder: prefisso ricostruito -> stesso modello -> stessa CDF -> range decoder -> nuovo byte.

### Rischio centrale
Nei modelli neurali la distribuzione nasce da floating point. “Numericamente vicino” non è sufficiente se una differenza cambia i confini cumulativi. Serve un contratto esplicito di quantizzazione e, se necessario, una reference inference path.

### Test permanenti
- empty input;
- singolo byte;
- tutti i 256 simboli;
- pattern periodici;
- input pseudocasuali con seed;
- file reali piccoli;
- hash originale = hash decodificato.

### Collegamento alla ricerca
Il determinismo cross-backend può diventare un tema di ricerca indipendente. PyTorch e MLX possono essere equivalenti per training senza essere automaticamente intercambiabili all'interno dello stesso bitstream.
