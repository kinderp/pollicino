# UDA 1 · Lezione 1 — Dal file ai bit e ai byte · Note docente

## Scopo concettuale

Questa lezione fissa il livello di rappresentazione su cui lavorerà POLLICINO: una sequenza finita su un alfabeto di cardinalità 256.

Formalmente, un file di `N` byte è un elemento di:

```text
{0, ..., 255}^N
```

equivalentemente di:

```text
{0,1}^{8N}
```

Il numero di possibili stringhe di lunghezza esatta `N` byte è:

```text
256^N = 2^(8N)
```

È importante che gli studenti comprendano subito la distinzione tra **sintassi binaria** e **semantica**. Un compressore lossless opera sulla rappresentazione; un modello può sfruttare regolarità che derivano dalla semantica senza che la semantica sia necessaria per definire il problema.

## Obiettivi disciplinari

- rappresentazione binaria dell'informazione;
- sistemi di numerazione binario/esadecimale;
- cardinalità di uno spazio discreto;
- lettura raw di un file;
- introduzione al concetto di alfabeto.

## Collegamento scientifico

Indichiamo con:

```text
X_1, X_2, ..., X_N
```

i byte di un file, con `X_i` appartenente a un alfabeto `A` di 256 simboli.

Questo ci permetterà più avanti di definire:

```text
P(X_i | X_<i)
```

e quindi la code length ideale:

```text
-log2 P(X_i | X_<i)
```

L'intero corso può essere visto come il tentativo di costruire modelli sempre migliori di questa distribuzione condizionata.

## Nota combinatoria

Se consideriamo **tutti i file fino a N byte**, e ammettiamo anche il file vuoto, il numero non è `256^N` ma:

```text
1 + 256 + 256^2 + ... + 256^N
```

cioè una serie geometrica:

```text
(256^(N+1) - 1) / 255
```

Questa distinzione sarà utile nella lezione sugli hash: il dominio dei possibili file cresce esponenzialmente.

## Strategia didattica

1. Partire da file reali scelti dagli studenti.
2. Mostrare gli stessi file in un editor normale e come hex.
3. Chiedere: «dove sta scritto che questo è un PNG?»
4. Arrivare al concetto di magic number/header senza trasformare la lezione in una trattazione dei formati.
5. Concludere mostrando che, per POLLICINO, il primo alfabeto sarà deliberatamente universale: 256 byte.

## Errori tipici

- «Un byte contiene numeri da 0 a 256»: correggere in **0–255**, 256 valori.
- confondere KB con Kb;
- pensare che estensione e contenuto siano la stessa cosa;
- credere che la sequenza binaria porti da sola il significato;
- dire che un file da `N` byte contiene `N` bit.

## Approfondimento per il docente

La scelta byte-level evita un tokenizer BPE e rende trasparente la connessione con la compressione lossless. Il prezzo è una sequenza più lunga rispetto alla tokenizzazione testuale. Per POLLICINO questo trade-off è desiderabile: ogni possibile file è rappresentabile senza vocabolari specifici del dominio.

## Verifica rapida

La risposta chiave all'exit ticket è **256**.

Per la domanda `10101100`:

```text
1010 = A
1100 = C
=> AC
```

## Ponte alla lezione 2

Una volta definito l'enorme spazio di possibili file possiamo chiedere:

> Possiamo assegnare a ciascun file un identificatore molto più corto e poi ricostruire il file dall'identificatore?

La risposta conduce direttamente a principio dei cassetti, collisioni e funzioni hash.
