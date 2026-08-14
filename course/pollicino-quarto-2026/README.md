# POLLICINO - corso 2026/2027

Questo directory è un **course bundle auto-contenuto compatibile con il formato di `2cornot2c` / TheBitLab**.

## Una lezione, due profondità

Ogni lezione ha un unico ID concettuale e tre artefatti sincronizzati:

- `handouts/`: teoria e attività per gli studenti;
- `materials/`: teoria scientifica, derivazioni, note didattiche e soluzioni per il docente;
- `activities/`: scheda JSON TheBitLab per svolgimento, metriche e collegamento alla UDA.

La teoria non viene scritta due volte in modo indipendente: i due livelli devono restare allineati sugli stessi obiettivi, simboli, esempi chiave e risultati.

## Mappa del corso

1. **UDA 1 - Informazione, bit, probabilità ed entropia**
2. **UDA 2 - Compressione come predizione**
3. **UDA 3 - Dalla statistica alle reti neurali**
4. **UDA 4 - Costruire un Transformer**
5. **UDA 5 - Byte language model con PyTorch e MLX**
6. **UDA 6 - Codec POLLICINO e ricerca sperimentale**

## Convenzione degli ID

Le lezioni usano `lNN-*` e le activity dichiarano nel campo `contesto.uda` la UDA a cui appartengono.

Esempio:

```text
uda-01-informazione
  l01-file-byte
  l02-hash-collisioni
  l03-informazione-probabilita
  l04-entropia-baseline
```

## Stato

La **UDA 1 è il primo modulo completo**. Le UDA successive sono già dichiarate nel manifest e verranno popolate in ordine, mantenendo la parità docente/studenti.
