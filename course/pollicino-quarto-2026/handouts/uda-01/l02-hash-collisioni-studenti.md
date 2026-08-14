# UDA 1 · Lezione 2 — Hash, collisioni e perché un'impronta non contiene il file

## Domanda guida

**Se conosco lo SHA-256 di un file, posso ricostruirlo?**

Questa domanda è all'origine di POLLICINO.

## Obiettivi

Alla fine della lezione saprai:

- descrivere una funzione hash come mappa da dati di lunghezza variabile a un output di lunghezza fissa;
- spiegare il principio dei cassetti;
- distinguere hash, compressione e cifratura;
- spiegare perché devono esistere collisioni;
- capire che un hash può verificare un file senza contenere abbastanza informazione per ricostruirlo.

## 1. Una funzione che produce un'impronta

Una funzione hash prende un input e produce un valore di lunghezza fissata.

Esempio concettuale:

```text
file -----------------> hash di 256 bit
```

SHA-256 produce 256 bit, cioè 32 byte, qualunque sia la dimensione del file.

## 2. Il principio dei cassetti

Immagina:

- 10 oggetti;
- 3 cassetti.

Se metti ogni oggetto in un cassetto, almeno un cassetto deve contenere più di un oggetto.

Lo stesso succede con gli hash.

SHA-256 può produrre:

```text
2^256
```

valori diversi.

Ma i possibili file sono molti di più. Quindi file diversi **devono** condividere qualche valore hash.

Quando due input diversi producono lo stesso hash abbiamo una:

> **collisione**

## 3. Perché allora SHA-256 è utile?

Una buona funzione crittografica rende estremamente difficile trovare volontariamente:

- un input che produca un hash assegnato;
- due input diversi con lo stesso hash.

Questo non elimina matematicamente le collisioni: le rende difficili da trovare.

## 4. Hash ≠ compressione

Supponiamo:

```text
film.mkv     4 GB
SHA-256      32 byte
```

Abbiamo davvero compresso 4 GB in 32 byte?

No.

Se fosse una compressione lossless universale, quei 32 byte dovrebbero permettere di scegliere **un solo** file tra tutti i possibili file da 4 GB. Ma 256 bit non bastano.

L'hash funziona bene per rispondere alla domanda:

> «Il file che ho ricevuto è proprio quello atteso?»

non alla domanda:

> «Qual era il file originale?»

## 5. Una metafora

Un hash è più simile al **numero di una targa** che all'automobile.

Se esiste un database che associa targa → auto, la targa può aiutarti a trovarla. Ma la targa non contiene fisicamente tutte le informazioni dell'auto.

Questa osservazione sarà fondamentale più avanti: un **modello condiviso** può svolgere il ruolo di conoscenza comune che restringe le possibilità.

## Esercizi

1. Un hash di 8 bit può assumere quanti valori?
2. Se applichiamo un hash di 8 bit a 300 file distinti, possiamo evitare tutte le collisioni?
3. Perché un hash più corto del file non è automaticamente una compressione?
4. Scrivi una frase che distingua:
   - hashing;
   - compressione lossless;
   - cifratura.
5. Se mittente e destinatario possiedono già lo stesso database di un milione di file, quante informazioni circa servono per scegliere uno dei file? Non calcolare ancora: fai un'ipotesi.

## Laboratorio Python

```python
from hashlib import sha256
from pathlib import Path

data = Path("esempio.txt").read_bytes()
print(sha256(data).hexdigest())
```

Modifica un solo carattere nel file e confronta l'hash.

## Exit ticket

Vero o falso?

> «Poiché SHA-256 produce 256 bit, ogni file può essere ricostruito esattamente a partire dai suoi 256 bit di hash.»
