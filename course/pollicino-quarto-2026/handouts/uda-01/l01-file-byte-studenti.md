# UDA 1 · Lezione 1 — Dal file ai bit e ai byte

## Domanda guida

**Che cosa c'è davvero dentro un file?**

Quando apriamo una fotografia, un PDF o un programma vediamo oggetti molto diversi. Il computer, però, memorizza tutti questi file come una sequenza di bit.

## Obiettivi

Alla fine della lezione saprai:

- distinguere bit, byte e sequenza di byte;
- spiegare perché file diversi possono essere rappresentati con lo stesso alfabeto di 256 byte;
- convertire piccoli numeri tra decimale, binario ed esadecimale;
- leggere i primi byte di un file;
- calcolare quante sequenze diverse esistono usando un certo numero di bit.

## 1. Il bit

Un **bit** può assumere due valori:

```text
0 oppure 1
```

Con un solo bit possiamo rappresentare 2 possibilità. Con due bit:

```text
00  01  10  11
```

abbiamo 4 possibilità.

Con `n` bit abbiamo:

```text
2^n
```

sequenze possibili.

## 2. Il byte

Un **byte** è formato da 8 bit.

Poiché:

```text
2^8 = 256
```

un byte può assumere 256 valori diversi, da 0 a 255.

Per questo nel progetto POLLICINO useremo spesso un vocabolario molto semplice:

```text
{0, 1, 2, ..., 255}
```

Più avanti un modello proverà a prevedere **quale dei 256 byte verrà dopo**.

## 3. Perché usiamo l'esadecimale

Scrivere otto bit alla volta è scomodo:

```text
11101010
```

In esadecimale lo stesso byte si scrive:

```text
EA
```

Ogni cifra esadecimale rappresenta 4 bit.

| Decimale | Binario | Hex |
|---:|---:|---:|
| 0 | 0000 | 0 |
| 10 | 1010 | A |
| 15 | 1111 | F |
| 255 | 11111111 | FF |

## 4. Un file come sequenza

Immaginiamo un file di 4 byte:

```text
50 4F 4C 00
```

Dal punto di vista del sistema è una sequenza di quattro simboli scelti tra 256 possibilità.

Il significato dipende da **come interpretiamo** quei byte. La stessa sequenza può essere letta come numeri, caratteri, parti di un'immagine o dati di un formato.

Questa distinzione sarà importante:

> **I byte sono la rappresentazione; il significato dipende dal formato e dal programma che li interpreta.**

## 5. Quanti file sono possibili?

Un file lungo un byte ha:

```text
256 = 2^8
```

contenuti possibili.

Un file lungo due byte ha:

```text
256^2 = 2^16 = 65 536
```

contenuti possibili.

Un file di `N` byte ha:

```text
256^N = 2^(8N)
```

possibili sequenze.

Già per file molto piccoli il numero cresce in modo enorme.

## Laboratorio

Con Python:

```python
from pathlib import Path

data = Path("esempio.txt").read_bytes()

print("Byte:", len(data))
print("Primi 16 byte:", data[:16])
print("Hex:", data[:16].hex(" "))
```

Prova con:

1. un file `.txt`;
2. una piccola immagine;
3. un file `.zip`.

Osserva: per Python sono sempre sequenze di byte.

## Prova tu

1. Quante sequenze diverse possiamo costruire con 3 bit?
2. Quanti valori contiene un byte?
3. Quanti file diversi di esattamente 2 byte possono esistere?
4. Converti `10101100` in esadecimale.
5. Spiega con parole tue la differenza tra **contenuto binario** e **significato del file**.

## Exit ticket

Completa la frase:

> Un modello byte-level non deve conoscere in anticipo se sta leggendo testo, immagine o codice: riceve sempre una sequenza di ______ possibili simboli.
