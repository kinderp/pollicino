# UDA 1 · Lezione 3 — Probabilità, sorpresa e quantità di informazione

## Domanda guida

**Perché un evento raro ci dà più informazione di un evento quasi certo?**

## Obiettivi

Alla fine della lezione saprai:

- collegare probabilità e quantità di informazione;
- interpretare `-log2(p)` come costo ideale in bit;
- calcolare semplici quantità di informazione;
- capire perché una previsione migliore può diventare una compressione migliore.

## 1. Informazione e sorpresa

Considera due messaggi:

```text
A. Domani il Sole sorgerà.
B. Domani nevicherà nel deserto del Sahara.
```

Il secondo messaggio, se vero, ci sorprende molto di più.

Intuitivamente:

- evento molto probabile → poca nuova informazione;
- evento raro → molta nuova informazione.

## 2. La formula

Per un evento con probabilità `p` definiamo la quantità di informazione:

```text
I = -log2(p)
```

L'unità è il **bit**.

Non pensare al logaritmo come a una formula da imparare a memoria. Qui risponde alla domanda:

> «Quante scelte binarie servono, idealmente, per distinguere un evento con questa probabilità?»

## 3. Casi semplici

Se:

```text
p = 1/2
```

allora:

```text
I = 1 bit
```

Se:

```text
p = 1/4
```

allora:

```text
I = 2 bit
```

Se:

```text
p = 1/8
```

allora:

```text
I = 3 bit
```

Perché?

```text
1/2 = 2^-1
1/4 = 2^-2
1/8 = 2^-3
```

## 4. Il caso dei byte

Se tutti i 256 byte sono ugualmente probabili:

```text
p = 1/256 = 2^-8
```

quindi ogni byte porta:

```text
8 bit
```

di informazione.

Questo sarà il nostro **punto zero**.

## 5. Se sappiamo prevedere meglio

Immagina che un modello, osservato il contesto, assegni al byte corretto probabilità:

```text
p = 1/2
```

Il suo costo ideale diventa 1 bit invece di 8.

Se assegna:

```text
p = 1/4
```

il costo è 2 bit.

Il collegamento fondamentale di POLLICINO è:

> **prevedere bene significa assegnare alta probabilità al dato reale; alta probabilità significa minore costo informativo.**

## Esercizi

Calcola `-log2(p)` per:

1. `p = 1/2`
2. `p = 1/4`
3. `p = 1/16`
4. `p = 1/256`

Poi rispondi:

5. Quale evento costa più bit: uno con `p = 1/2` o uno con `p = 1/32`?
6. Se un modello assegna probabilità molto bassa proprio al simbolo che arriva davvero, il costo aumenta o diminuisce?
7. Perché una buona previsione del byte successivo può aiutare un compressore?

## Mini-esperimento Python

```python
from math import log2

probabilita = [1/2, 1/4, 1/8, 1/16, 1/256]

for p in probabilita:
    print(p, -log2(p))
```

## Exit ticket

Completa:

> Se un modello assegna probabilità più ______ al simbolo che accade davvero, il numero ideale di bit necessari per descriverlo diventa più ______.
