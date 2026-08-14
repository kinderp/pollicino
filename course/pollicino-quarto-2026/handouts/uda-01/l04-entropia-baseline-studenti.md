# UDA 1 · Lezione 4 — Entropia di Shannon e baseline degli 8 bit/byte

## Domanda guida

**Quanto è imprevedibile, in media, una sorgente di dati?**

## Obiettivi

Alla fine della lezione saprai:

- interpretare l'entropia come informazione media;
- calcolare l'entropia di distribuzioni semplici;
- spiegare perché una distribuzione uniforme su 256 byte vale 8 bit/byte;
- distinguere entropia del dato e qualità di un modello;
- eseguire la baseline uniforme di POLLICINO.

## 1. Dall'informazione di un evento alla media

Nella lezione precedente abbiamo visto:

```text
I(x) = -log2 P(x)
```

L'entropia di Shannon è la media pesata di questa quantità:

```text
H(X) = - Σ p(x) log2 p(x)
```

Possiamo leggerla così:

> **quanti bit di nuova informazione produce in media questa sorgente?**

## 2. Moneta equa

Due risultati:

```text
P(testa) = 1/2
P(croce) = 1/2
```

Ogni risultato costa 1 bit.

Quindi:

```text
H = 1 bit
```

## 3. Moneta molto sbilanciata

Supponiamo:

```text
P(testa) = 0.99
P(croce) = 0.01
```

Il risultato è molto più prevedibile.

L'entropia è quindi **minore di 1 bit**.

La regola intuitiva:

> più una sorgente è prevedibile, minore è la sua entropia.

## 4. I 256 byte equiprobabili

Se ogni byte ha:

```text
p = 1/256
```

allora:

```text
H = 8 bit/byte
```

Questa è la baseline uniforme di POLLICINO.

Un modello che non sa nulla sul file può dire soltanto:

```text
"ognuno dei 256 byte è ugualmente probabile"
```

## 5. Un file ripetitivo

Un file composto quasi solo da:

```text
AAAAAAAAAAAAAAAAAAAA...
```

non usa i byte con la stessa frequenza.

La distribuzione è molto concentrata e la sua entropia empirica può essere molto più bassa di 8 bit/byte.

Attenzione: questo non significa automaticamente che qualsiasi algoritmo raggiungerà esattamente quell'entropia. È un riferimento teorico.

## Laboratorio POLLICINO

Dopo aver installato il progetto in modalità sviluppo:

```bash
python -m pollicino.baselines.uniform percorso/del/file
```

La baseline deve riportare:

```text
8.000000 bit/byte
```

e verificare che il round-trip sia identico tramite SHA-256.

Prova almeno:

1. un file di testo;
2. un file con molti caratteri ripetuti;
3. un file casuale;
4. un file già compresso, per esempio `.zip`.

La baseline uniforme resterà sempre 8 bit/byte perché **non impara nulla dai dati**.

## Esercizio Python: frequenze

```python
from collections import Counter
from pathlib import Path

data = Path("esempio.txt").read_bytes()
counts = Counter(data)

for byte, n in counts.most_common(10):
    print(byte, n / len(data))
```

Questa è la porta verso la prossima UDA: invece di assumere probabilità uniformi, possiamo **imparare le probabilità dai dati**.

## Domande

1. Qual è l'entropia di una moneta equa?
2. Una moneta sempre testa ha entropia alta o bassa?
3. Perché la sorgente uniforme di 256 byte dà 8 bit/byte?
4. Se un modello assegna probabilità migliori rispetto alla distribuzione uniforme, quale metrica vogliamo far scendere?
5. Perché i dati casuali saranno un importante controllo negativo?

## Exit ticket

Scrivi in una riga la catena concettuale:

```text
probabilità -> ______ -> previsione -> compressione
```
