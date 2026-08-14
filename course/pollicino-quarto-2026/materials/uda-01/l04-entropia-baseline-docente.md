# UDA 1 · Lezione 4 — Entropia, cross-entropy e baseline uniforme · Note docente

## Entropia di Shannon

Per una variabile discreta `X` con distribuzione `p`:

```text
H(X) = - Σ_x p(x) log2 p(x)
```

equivalentemente:

```text
H(X) = E_p[-log2 p(X)]
```

L'unità è bit per simbolo.

Per un alfabeto di 256 simboli, l'entropia massima è raggiunta dalla distribuzione uniforme:

```text
H_max = log2 256 = 8 bit/byte
```

## Due quantità da non confondere

### Entropia della sorgente

```text
H(p) = E_p[-log2 p(X)]
```

dipende dalla distribuzione reale `p`.

### Cross-entropy del modello

Se il modello usa una distribuzione `q`:

```text
H(p,q) = E_p[-log2 q(X)]
```

e vale:

```text
H(p,q) = H(p) + D_KL(p || q)
```

quindi:

```text
H(p,q) >= H(p)
```

L'uguaglianza si ha quando `q = p` (quasi ovunque sul supporto).

Questa è una delle relazioni centrali per il percorso scientifico: il divario tra entropia e cross-entropy è dovuto alla divergenza KL, cioè all'imperfezione del modello.

## Bits per byte

Nel progetto useremo:

```text
bpb = -(1/N) Σ_i log2 q(x_i | x_<i)
```

Per il modello uniforme:

```text
q(x_i | x_<i) = 1/256
```

per ogni byte e contesto, quindi:

```text
bpb = 8
```

su **qualsiasi file non vuoto**.

La baseline uniforme non è un compressore utile: è un controllo sperimentale e una verifica delle metriche.

## Perché il random è un controllo negativo

Per dati generati in modo indipendente e uniforme sui 256 byte, nessun modello che non possieda side information dovrebbe ottenere sistematicamente una code length inferiore a 8 bit/byte sul lungo periodo. Risultati sorprendentemente inferiori richiedono di verificare:

- data leakage;
- metadati non conteggiati;
- uso del seed come side information;
- costo del modello ignorato;
- bug nella misura;
- confronto non omogeneo.

## Entropia empirica e dipendenze

La frequenza marginale dei byte cattura solo una distribuzione di ordine zero. Un file può avere distribuzione marginale quasi uniforme ma forti dipendenze sequenziali.

Esempio artificiale: alternanza deterministica tra due simboli. Il modello marginale non sfrutta il contesto, mentre un modello condizionato può prevedere il prossimo simbolo quasi perfettamente.

Questo prepara:

```text
uniforme
-> frequenze
-> bigrammi
-> n-gram / Markov
-> neural predictor
-> Transformer
```

## Compressione reale

L'entropia/cross-entropy produce una code length ideale. Per trasformarla in un bitstream decodificabile useremo più avanti arithmetic/range coding.

Va mantenuta la separazione:

```text
predictor -> probabilità
coder     -> bitstream
```

Il Transformer non è da solo il compressore lossless: diventa parte del codec quando le sue probabilità sono accoppiate a un entropy coder deterministico.

## Attività laboratoriale

Eseguire la baseline su almeno quattro categorie:

- testo;
- dati ripetitivi;
- random uniforme;
- dati già compressi.

La baseline deve restare 8 bpb. La variazione arriverà nella UDA 2 con modelli appresi.

## Soluzioni rapide

1. moneta equa: 1 bit.
2. moneta deterministica: 0 bit nel modello ideale.
3. uniforme su 256: `log2 256 = 8`.
4. vogliamo ridurre cross-entropy / bpb.
5. random serve a mostrare il limite di incomprimibilità e a rilevare errori/leakage.

Exit ticket suggerito:

```text
probabilità -> informazione/entropia -> previsione -> compressione
```

## Ponte alla UDA 2

La domanda successiva è operativa:

> Se il file non è uniforme, come stimiamo `q(byte)` e quanto guadagniamo rispetto agli 8 bpb?

La UDA 2 inizierà con frequenze empiriche e codici classici, prima di introdurre il contesto.
