# UDA 1 · Lezione 2 — Hash, collisioni e impossibilità della ricostruzione universale · Note docente

## Risultato centrale

Una funzione:

```text
h : X -> {0,1}^k
```

con dominio `X` più grande di `2^k` non può essere iniettiva.

Se consideriamo file arbitrariamente lunghi, il dominio è infinito mentre il codominio di SHA-256 contiene esattamente `2^256` valori. Per il principio dei cassetti esistono necessariamente collisioni.

Questo è il limite matematico della prima intuizione di POLLICINO: **un fingerprint corto, da solo, non identifica un file arbitrario in modo lossless**.

## Distinzioni da fissare

### Hashing
Trasforma dati arbitrari in un digest fisso. Obiettivi crittografici tipici: preimage resistance, second-preimage resistance, collision resistance.

### Compressione lossless
Definisce una codifica decodificabile senza ambiguità sul dominio considerato. Il decoder deve recuperare l'input esatto.

### Cifratura
Trasforma plaintext in ciphertext usando una chiave; l'obiettivo è la confidenzialità, non la riduzione della lunghezza.

Gli studenti tendono a confondere le tre categorie perché tutte trasformano byte in altri byte.

## La vera intuizione da salvare

La parte utile dell'idea originale non è:

```text
short hash -> file
```

ma:

```text
conoscenza condivisa + pochi bit di disambiguazione -> file
```

Se il decoder sa già che l'oggetto appartiene a un insieme di `M` candidati equiprobabili, identificare il candidato richiede idealmente circa:

```text
log2(M)
```

bit.

Questo prepara la lezione 3 sull'informazione e, molto più avanti, la linea di ricerca `model + fingerprint + candidate search`.

## Esempio didattico

Con 8 bit abbiamo 256 digest.

Se il dominio contiene esattamente 256 oggetti, **potrebbe** esistere una codifica biunivoca da 8 bit, ma una generica funzione hash non promette questa proprietà.

Se il dominio contiene 257 oggetti, nessuna funzione a 8 bit può essere iniettiva.

Questo esempio separa bene:
- limite di cardinalità;
- proprietà specifiche della funzione.

## Birthday bound

Per il percorso docente, ricordare che il principio dei cassetti garantisce collisioni, mentre il birthday paradox riguarda la probabilità di incontrarne una campionando input. Per un hash ideale di `k` bit, una collisione diventa plausibile dopo circa `2^(k/2)` campioni. Non è necessario introdurlo agli studenti in questa lezione.

## Nota crittografica

Non presentare «one-way» come impossibilità matematica di inversione. La resistenza alla preimmagine è una proprietà computazionale: per un digest dato, trovare un input che lo produca deve essere impraticabile. Inoltre, a causa delle collisioni, parlare de *l'originale* senza ulteriore informazione è semanticamente scorretto.

## Soluzioni rapide

1. Hash di 8 bit: `2^8 = 256`.
2. 300 file distinti verso 256 digest: almeno una collisione è obbligatoria.
3. Un digest non fornisce una decodifica univoca dell'intero dominio.
4. Exit ticket: **falso**.

## Ponte alla lezione 3

La domanda 5 introduce il concetto chiave:

> Quanti bit servono per scegliere una possibilità tra `M` alternative?

La risposta `log2(M)` porta naturalmente alla self-information `-log2 p`.
