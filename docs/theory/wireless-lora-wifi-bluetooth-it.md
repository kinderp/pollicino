# Modulo teorico — Wireless, LoRa, Wi-Fi e Bluetooth

Questo modulo estende la Theory Map di Pollicino con il livello di comunicazione fisica e di rete necessario a comprendere PollicinoNet.

L'obiettivo non è imparare a memoria sigle e velocità, ma capire i **trade-off** che collegano:

```text
frequenza
  ↕
ampiezza di banda
  ↕
modulazione / codifica
  ↕
potenza
  ↕
sensibilità
  ↕
distanza
  ↕
airtime
  ↕
energia
  ↕
throughput
  ↕
affidabilità
```

---

## 1. Che cosa significa "wireless"

Una comunicazione wireless trasferisce informazione usando onde elettromagnetiche invece di un conduttore fisico.

Per analizzare un collegamento bisogna separare almeno quattro livelli:

1. **segnale fisico**: frequenza, potenza, rumore, modulazione;
2. **frame/link**: pacchetti, CRC, accesso al mezzo, ritrasmissioni;
3. **rete**: indirizzamento, routing, relay, discovery;
4. **applicazione**: file, messaggi, sensori, voce, video.

PollicinoNet deve poter cambiare il livello fisico senza cambiare il significato dell'oggetto trasportato.

---

## 2. Frequenza e lunghezza d'onda

La frequenza `f` indica quante oscillazioni avvengono in un secondo.

La lunghezza d'onda `λ` è legata alla frequenza da:

```text
λ = c / f
```

dove `c` è la velocità di propagazione dell'onda elettromagnetica nel mezzo, approssimata con la velocità della luce nel vuoto quando si fa un primo calcolo.

Esempio qualitativo:

- LoRa europeo sub-GHz: circa 868 MHz;
- Bluetooth LE: 2.4 GHz;
- Wi-Fi: famiglie che operano, a seconda dello standard e della regione, nelle bande 2.4, 5 e 6 GHz.

Frequenze, antenne, ostacoli e regolamentazione influenzano fortemente il comportamento reale.

---

## 3. Potenza e dBm

Nel mondo radio la potenza viene spesso espressa in **dBm**.

```text
P[dBm] = 10 log10(P[mW])
```

Valori utili:

```text
0 dBm   = 1 mW
10 dBm  = 10 mW
20 dBm  = 100 mW
```

Nel laboratorio HW-001 abbiamo usato 10 dBm, cioè circa 10 mW di potenza nominale configurata al trasmettitore.

Attenzione: la potenza impostata nel chip non coincide automaticamente con la potenza effettivamente irradiata. Antenna, perdite, PCB e regolamentazione contano.

---

## 4. RSSI

RSSI è una misura della potenza ricevuta.

Nel primo test PollicinoNet abbiamo osservato valori intorno a:

```text
-40 dBm
```

Un valore di `-40 dBm` indica un segnale più potente di `-100 dBm`.

Non esiste però una soglia RSSI universale per dire "funziona". Dipende da:

- ricevitore;
- modulazione;
- bandwidth;
- spreading factor;
- rumore;
- interferenze;
- implementazione.

---

## 5. Rumore e SNR

SNR significa **Signal-to-Noise Ratio**.

In decibel:

```text
SNR[dB] = P_segnale[dB] - P_rumore[dB]
```

Un SNR positivo significa che il segnale misurato è sopra il rumore nella metrica usata.

Una proprietà importante di LoRa è la possibilità di ricevere in condizioni di SNR molto basso; per questo non bisogna applicare intuitivamente a LoRa le stesse aspettative di una radio ad alto throughput.

---

## 6. Bandwidth

La bandwidth è l'ampiezza di banda occupata/elaborata dal canale.

In generale, maggiore bandwidth può consentire tempi simbolo più brevi e più throughput, ma cambia anche:

- rumore integrato dal ricevitore;
- sensibilità;
- airtime;
- robustezza;
- occupazione dello spettro.

HW-001 usa:

```text
BW = 125 kHz
```

---

## 7. Modulazione e codifica

La modulazione definisce come i bit vengono rappresentati nel segnale radio.

Esempi di famiglie diverse:

- Wi-Fi moderno: PHY ad alto throughput basati su OFDM/OFDMA e tecniche multi-carrier/multi-antenna;
- Bluetooth LE: PHY basati su GFSK, con varianti di velocità e coded PHY;
- LoRa: modulazione spread-spectrum basata su chirp.

La **codifica di canale** aggiunge ridondanza per aumentare la probabilità di recuperare i dati in presenza di errori.

La ridondanza costa airtime ma può evitare ritrasmissioni.

---

## 8. LoRa: PHY, non rete

È fondamentale distinguere:

```text
LoRa
=
livello fisico/modulazione radio
```

mentre:

```text
LoRaWAN
=
protocollo di rete LPWAN costruito sopra LoRa
```

LoRaWAN tipicamente usa una topologia star-of-stars con gateway IP e network server.

PollicinoNet HW-001 e FreakWAN usano invece **bare LoRa**, cioè pacchetti LoRa senza adottare LoRaWAN come stack di rete.

Questo significa che routing, addressing, ACK, retry, discovery, sicurezza e applicazione sono responsabilità del software che costruiamo sopra il PHY.

---

## 9. Chirp Spread Spectrum

LoRa usa una forma di Chirp Spread Spectrum.

Un chirp varia la propria frequenza durante il simbolo. L'informazione viene codificata nella struttura temporale/frequenziale dei chirp.

Il vantaggio progettuale è un forte trade-off tra:

- velocità;
- sensibilità;
- robustezza;
- airtime.

Questo è il motivo per cui LoRa può essere molto utile quando dobbiamo trasferire pochi bit su distanze o condizioni difficili, ma non è la scelta naturale per streaming ad alto bitrate.

---

## 10. Spreading Factor

Lo spreading factor viene normalmente indicato come `SF`.

Sul nostro SX1276 le configurazioni LoRa usate comunemente coprono SF6…SF12; HW-001 usa:

```text
SF7
```

A parità di bandwidth, aumentando SF aumenta fortemente la durata del simbolo e quindi l'airtime, ma migliora la capacità di operare con segnali più deboli.

Una relazione didattica fondamentale è:

```text
T_symbol = 2^SF / BW
```

Con HW-001:

```text
SF = 7
BW = 125000 Hz

T_symbol ≈ 128 / 125000
         ≈ 1.024 ms
```

A SF12, con la stessa bandwidth, il simbolo diventerebbe molto più lungo.

Questa crescita esponenziale è uno dei motivi per cui il parametro SF va scelto con attenzione.

---

## 11. Coding Rate LoRa

HW-001 usa:

```text
CR = 4/5
```

In modo intuitivo: ai dati utili viene aggiunta ridondanza per la protezione dagli errori.

Più ridondanza può migliorare la robustezza, ma aumenta il costo radio.

Per PollicinoNet non basta quindi chiedere:

> quanti byte sto inviando?

Dobbiamo chiedere:

> quanto airtime, quanta energia e quante ritrasmissioni servono per ottenere una ricostruzione verificata?

Da qui nasce il TRC.

---

## 12. Airtime

L'airtime è il tempo durante il quale il canale radio viene occupato da una trasmissione.

Dipende almeno da:

- payload;
- preamble;
- SF;
- bandwidth;
- coding rate;
- header;
- CRC;
- impostazioni del modem.

Due messaggi con lo stesso numero di byte possono avere airtime molto diverso con parametri PHY differenti.

Per questo HW-002 misurerà/validerà il costo radio di pacchetti di dimensioni diverse.

---

## 13. Duty cycle

Duty cycle significa percentuale di tempo in cui il trasmettitore occupa il canale in una determinata finestra temporale.

Dal punto di vista scientifico è utile anche prima di parlare di norme:

```text
molto airtime
→
più consumo
→
più probabilità di collisione
→
meno capacità condivisa
```

La normativa reale dipende da regione, banda, sottobanda e modalità operativa e deve essere verificata prima di test estesi o deployment.

---

## 14. CRC, FEC, ACK e retry non sono la stessa cosa

### CRC

Serve soprattutto a **rilevare** che il frame è corrotto.

### FEC

Introduce ridondanza per tentare di **correggere** alcuni errori senza richiedere una nuova trasmissione.

### ACK

Conferma che qualcosa è stato ricevuto secondo un certo contratto.

### Retry

Ripete una trasmissione quando il protocollo ritiene che il risultato non sia stato ottenuto.

PollicinoNet deve contabilizzare questi costi separatamente.

---

## 15. Wi-Fi

Wi-Fi appartiene alla famiglia IEEE 802.11 ed è progettato come WLAN ad alto throughput.

Caratteristiche tipiche del problema che risolve:

- rete locale IP;
- throughput elevato;
- bassa latenza rispetto a LPWAN;
- trasferimento di grandi quantità di dati;
- infrastruttura AP/client o forme peer-to-peer previste dallo stack.

Le famiglie moderne operano in spettro non licenziato nelle bande 2.4, 5 e, per gli standard/regioni che lo prevedono, 6 GHz.

Il prezzo da pagare rispetto a LoRa è un diverso punto del trade-off energia/range/throughput.

---

## 16. Bluetooth e Bluetooth Low Energy

Bluetooth opera nella banda ISM a 2.4 GHz.

Bluetooth LE è progettato per bassi consumi e supporta differenti PHY e topologie, tra cui point-to-point, broadcast e mesh.

Non bisogna ridurre Bluetooth a "pochi metri": il range reale dipende da PHY, potenza, sensibilità, antenna e ambiente. Il Bluetooth SIG evidenzia esplicitamente questo trade-off.

Per PollicinoNet, BLE è interessante come:

- configurazione locale;
- discovery vicino;
- canale di controllo;
- possibile handover più ricco di LoRa a breve distanza.

---

## 17. Confronto concettuale

| Tecnologia | Problema tipico | Throughput | Energia | Range | Infrastruttura | Uso PollicinoNet |
|---|---|---|---|---|---|---|
| LoRa bare | pochi dati su link molto scarso | molto basso | basso se usato con disciplina | potenzialmente molto ampio | nessuna obbligatoria | discovery, exact fallback, mesh sperimentale |
| LoRaWAN | IoT LPWAN gestito | molto basso | ottimizzato IoT | ampio | gateway + network server | possibile adapter, non core |
| Bluetooth LE | PAN / device-to-device | medio-basso/medio | molto basso | dipende fortemente dal PHY | nessuna obbligatoria | config, discovery, handover locale |
| Wi-Fi | WLAN / IP ad alto throughput | alto | maggiore | locale | AP spesso presente | rich link, retrieval, sync |
| Cellulare | WAN gestita dall'operatore | medio-alto/alto | variabile | vasta copertura infrastrutturata | rete operatore | rich link / Internet |

La tabella è qualitativa: non usare queste colonne come range o velocità garantite.

---

## 18. Perché LoRa è interessante per PollicinoNet

PollicinoNet parte da una domanda diversa da una normale rete:

> Qual è il minimo costo totale necessario per far arrivare al destinatario l'informazione utile o ricostruibile?

LoRa rende questa domanda particolarmente interessante perché ogni byte può essere costoso in airtime.

Esempi:

```text
oggetto già disponibile altrove
→ invia solo una coordinata
```

```text
ricevitore ha già alcuni chunk
→ invia solo i mancanti
```

```text
Internet disponibile dopo il rendezvous
→ LoRa fa discovery, Internet porta il contenuto
```

```text
nessun altro link disponibile
→ fallback EXACT su LoRa
```

---

## 19. LoRa vs LoRaWAN vs PollicinoNet vs FreakWAN

```text
SX1276
  ↓
LoRa PHY
  ↓
┌───────────────┬────────────────┬─────────────────┐
│ LoRaWAN       │ FreakWAN       │ PollicinoNet    │
│ standard LPWA │ WAN custom     │ content/network │
│ gateway/server│ flood routing  │ research layer  │
└───────────────┴────────────────┴─────────────────┘
```

FreakWAN e PollicinoNet possono quindi usare lo stesso PHY ma avere obiettivi e protocolli differenti.

---

## 20. Metriche da conoscere

### Throughput

Dati trasferiti per unità di tempo.

### Goodput

Dati **utili** consegnati per unità di tempo, escluso overhead inutile all'applicazione.

### Latency

Tempo tra richiesta/invio e risultato osservabile.

### Packet loss rate

Frazione di pacchetti che non raggiungono correttamente il destinatario.

### RSSI / SNR

Misure del link fisico.

### Airtime

Tempo di occupazione radio.

### Energy per useful bit

Energia spesa per ottenere informazione utile.

### TRC — Transmission Reconstruction Cost

Per PollicinoNet:

```text
TRC = discovery
    + rendezvous
    + manifest
    + payload mancante / residuale
    + FEC
    + ACK
    + ritrasmissioni
```

HW-002 inizierà a dare componenti fisiche a questa metrica.

---

## 21. Domande per gli studenti

1. Perché LoRa non è semplicemente "Wi-Fi che arriva più lontano"?
2. Che differenza c'è tra LoRa e LoRaWAN?
3. Perché aumentando SF aumenta l'airtime?
4. Perché un RSSI più vicino a zero indica maggiore potenza ricevuta?
5. È possibile avere un pacchetto con CRC valido ma applicazione logicamente sbagliata?
6. A cosa serve un ACK se abbiamo già il CRC?
7. Perché Bluetooth non ha un range unico definibile con un solo numero?
8. Perché PollicinoNet separa link scarso e rich link?
9. Quando può essere più conveniente inviare 40 byte di rendezvous invece di un file da 1 MB?
10. Perché il goodput è più interessante del bitrate nominale quando studiamo PollicinoNet?

---

## 22. Esperimenti didattici collegati

### Esperimento A — dBm

Convertire:

- 0 dBm;
- 10 dBm;
- 20 dBm;

in mW.

### Esperimento B — durata simbolo

Calcolare `T_symbol` con BW=125 kHz per:

- SF7;
- SF8;
- SF9;
- SF10;
- SF11;
- SF12.

Osservare il fattore di crescita.

### Esperimento C — HW-001

Interpretare i risultati reali:

```text
A→B: circa -40 dBm, SNR circa 9.5–9.8 dB
B→A: circa -36/-37 dBm, SNR circa 9.5–9.8 dB
```

Domanda: perché i due versi non devono necessariamente avere lo stesso RSSI?

### Esperimento D — HW-002

Misurare packet loss e RSSI/SNR al variare di:

- distanza;
- ostacoli;
- payload;
- SF;
- bandwidth;
- potenza.

Cambiare **una variabile alla volta**.

---

## 23. Fonti primarie consigliate

Per approfondire:

- Semtech, pagina prodotto SX1276 e datasheet SX1276/7/8/9;
- Semtech AN1200.22, *LoRa Modulation Basics*;
- LoRa Alliance, *What is LoRaWAN?* e LoRaWAN specifications;
- Bluetooth SIG, *Bluetooth Technology Overview* e *Bluetooth LE Primer*;
- IEEE 802.11 current/revision pages per le WLAN Wi-Fi;
- documentazione hardware LILYGO T3 V1.6.1;
- RadioLib documentation per il software radio usato in HW-001.

Le regole di utilizzo dello spettro non vanno dedotte da una guida didattica: prima di test radio estesi bisogna consultare la normativa/regional parameters correnti.
