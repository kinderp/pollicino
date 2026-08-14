# UDA 1 · Lezione 3 — Self-information e code length · Note docente

## Definizione

Per un evento `x` di probabilità `P(x) > 0`, la self-information è:

```text
I(x) = -log2 P(x)
```

Il logaritmo in base 2 produce una misura in bit.

## Perché il logaritmo

La scelta logaritmica rende additiva l'informazione di eventi indipendenti.

Se `x` e `y` sono indipendenti:

```text
P(x,y) = P(x)P(y)
```

allora:

```text
I(x,y)
= -log2(P(x)P(y))
= -log2 P(x) - log2 P(y)
= I(x) + I(y)
```

Questo è esattamente il comportamento desiderato per una lunghezza di codice.

## Connessione con POLLICINO

Per una sequenza autoregressiva:

```text
x_1, ..., x_N
```

la chain rule della probabilità dà:

```text
P(x_1, ..., x_N)
= Π_i P(x_i | x_<i)
```

Applicando `-log2`:

```text
-log2 P(x_1, ..., x_N)
= Σ_i -log2 P(x_i | x_<i)
```

Questa somma è la **ideal code length** del file sotto il modello.

È il ponte teorico diretto tra:
- language modeling;
- negative log-likelihood;
- cross-entropy;
- compressione entropica.

Quando più avanti alleneremo un Transformer minimizzando la cross-entropy, staremo contemporaneamente cercando di ridurre la lunghezza ideale della codifica.

## Attenzione didattica

Non dire ancora «un simbolo con probabilità 0.9 occupa 0.152 bit nel file» in senso letterale. Una singola codeword discreta non può avere una frazione di bit. I fractional bits sono una **lunghezza ideale media/logaritmica** che arithmetic coding può approssimare su sequenze.

Questa precisazione evita un equivoco importante.

## Esempi numerici

```text
p = 1/2    -> 1 bit
p = 1/4    -> 2 bit
p = 1/16   -> 4 bit
p = 1/256  -> 8 bit
p = 0.9    -> ~0.152 bit
p = 0.01   -> ~6.644 bit
```

Un modello può assegnare al simbolo corretto una probabilità inferiore a `1/256`; in quel caso il costo logaritmico supera 8 bit. Un modello cattivo può dunque essere peggiore della baseline uniforme.

## Collegamento ML

Se il target corretto è `y` e il modello produce una distribuzione `q`, la categorical cross-entropy per un singolo esempio one-hot è:

```text
CE = -log q(y)
```

Con log naturale otteniamo nats; dividendo per `ln(2)` otteniamo bit. Nella ricerca POLLICINO riporteremo preferibilmente **bits per byte (bpb)**.

## Soluzioni

- `1/2 -> 1`
- `1/4 -> 2`
- `1/16 -> 4`
- `1/256 -> 8`
- `1/32` costa più di `1/2`: 5 bit contro 1.
- probabilità bassa sul simbolo reale → costo maggiore.
- exit ticket: **alta**, **basso**.

## Ponte alla lezione 4

La self-information misura il costo di un singolo evento. L'entropia di Shannon sarà il suo valore medio atteso:

```text
H(X) = E[I(X)]
```
