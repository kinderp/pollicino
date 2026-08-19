# HW-001 — Guida pratica: dal PC al primo pacchetto PollicinoNet su LoRa

Questa guida riproduce, in modo didattico e verificabile, il laboratorio HW-001 con due schede **LILYGO / TTGO T3 V1.6.1 LoRa32** e radio **SX1276**.

L'obiettivo non è soltanto "far funzionare due schede". Alla fine del laboratorio lo studente deve saper distinguere:

- firmware e software host;
- porta seriale e collegamento radio;
- inizializzazione della radio e trasmissione effettiva;
- dato inviato, dato ricevuto e verifica byte-per-byte;
- RSSI e SNR;
- configurazione del PHY LoRa;
- prova unidirezionale e bidirezionale.

Il laboratorio è stato validato fisicamente con due unità reali: PND1 e PNF1 sono stati trasferiti in entrambe le direzioni senza modifica dei byte.

---

## 1. Materiale necessario

Per una postazione completa:

- 2 × LILYGO / TTGO T3 V1.6.1 LoRa32;
- 2 × antenne adatte alla variante 868 MHz;
- 2 × cavi **Micro-USB dati**;
- 1 PC Windows, Linux o macOS;
- Python 3;
- Git;
- accesso al repository Pollicino;
- nessuna microSD inserita durante il flash.

### Regola di sicurezza fondamentale

**Non trasmettere mai senza antenna collegata.**

Prima di alimentare una scheda che potrebbe andare in TX:

1. controllare che l'antenna sia montata;
2. verificare che l'antenna sia quella prevista per la banda della scheda;
3. non collegare batterie esterne se non necessarie al laboratorio;
4. per i primi test usare i parametri HW-001 congelati a bassa potenza.

Il firmware HW-001, appena avviato, entra in ricezione e non trasmette finché l'host non invia un comando `TX`.

---

## 2. Architettura del laboratorio

```text
PC
 | USB seriale
 v
LILYGO A / ESP32 / SX1276
 | LoRa 868.1 MHz
 v
LILYGO B / ESP32 / SX1276
 | USB seriale
 v
PC
```

Il firmware delle schede è volutamente un **bridge trasparente di byte**.

Host → scheda:

```text
TX <payload-esadecimale>
```

Scheda → host:

```text
RX <lunghezza> <RSSI> <SNR> <payload-esadecimale>
```

Il firmware non interpreta DNA, PND1, PNF1 o altri protocolli PollicinoNet. In questo modo il core PollicinoNet resta indipendente da LoRa.

---

## 3. Preparazione del repository

Aprire PowerShell o un terminale nella directory di lavoro.

Se il repository non è ancora presente:

```powershell
git clone https://github.com/kinderp/pollicino.git
cd pollicino
```

Se è già presente:

```powershell
git checkout main
git pull
```

Verificare Python:

```powershell
py --version
```

Su Linux/macOS può essere necessario usare:

```bash
python3 --version
```

---

## 4. Installazione degli strumenti

### 4.1 PlatformIO

HW-001 usa una versione congelata per rendere il build riproducibile:

```powershell
py -m pip install platformio==6.1.19
```

Verifica:

```powershell
pio --version
```

Se `pio` non viene trovato:

```powershell
py -m platformio --version
```

### 4.2 Pollicino come package Python + seriale

Il bridge host importa `pollicino.net`, quindi il repository va installato in modalità editable:

```powershell
py -m pip install -e . pyserial
```

Verifica:

```powershell
py -c "import pollicino; import pollicino.net; print('Pollicino OK')"
```

Output atteso:

```text
Pollicino OK
```

---

## 5. Identificare le porte seriali

Collegare **una sola scheda alla volta** nella fase iniziale.

Su Windows:

```powershell
pio device list
```

Oppure usare:

```text
Gestione dispositivi → Porte (COM e LPT)
```

Esempio del laboratorio validato:

```text
Board A -> COM3
Board B -> COM4
```

**Le porte COM non sono l'identità permanente della scheda.** Windows può assegnare numeri diversi su un altro PC o su un'altra porta USB.

---

## 6. Compilare il firmware

Dalla root del repository:

```powershell
pio run -d hardware/lilygo-lora32-v1.6.1
```

Ambiente validato HW-001:

- PlatformIO Core 6.1.19;
- `espressif32@6.13.0`;
- framework Arduino ESP32;
- RadioLib 7.6.0.

Il build HW-001 validato occupava circa il 7% della RAM disponibile e il 23.5% dello spazio applicativo configurato.

---

## 7. Flash della prima scheda

Con antenna collegata e microSD rimossa:

```powershell
pio run -d hardware/lilygo-lora32-v1.6.1 -t upload --upload-port COM3
```

Se `pio` non è nel PATH:

```powershell
py -m platformio run -d hardware/lilygo-lora32-v1.6.1 -t upload --upload-port COM3
```

Attendere `SUCCESS`.

---

## 8. Controllare il boot e l'inizializzazione radio

Aprire il monitor seriale:

```powershell
pio device monitor --port COM3 --baud 115200
```

Output atteso:

```text
READY hw-001
INFO board=lilygo-lora32-v1.6.1 chip=sx1276 freq_mhz=868.100 bw_khz=125.0 sf=7 cr=4/5 power_dbm=10 max_tx=240
```

### Perché `READY hw-001` è importante?

Nel firmware viene stampato **dopo** che l'inizializzazione della radio è riuscita. Quindi è una prova di:

- boot ESP32 corretto;
- comunicazione SPI con il transceiver;
- pinout compatibile;
- inizializzazione del driver SX1276;
- configurazione del PHY accettata dal dispositivo.

Le righe ESP32 come:

```text
rst:0x1 (POWERON_RESET)
boot:0x13 (SPI_FAST_FLASH_BOOT)
mode:DIO
```

sono messaggi di boot. In particolare `mode:DIO` in quel contesto indica la modalità di accesso alla flash e non è il DIO0/DIO1 della radio LoRa.

Chiudere il monitor con `Ctrl+C` prima che un altro programma tenti di aprire la stessa COM.

---

## 9. Flash della seconda scheda

Collegare la seconda scheda, con antenna montata.

Identificare la nuova porta, per esempio `COM4`:

```powershell
pio device list
```

Flash:

```powershell
pio run -d hardware/lilygo-lora32-v1.6.1 -t upload --upload-port COM4
```

Monitor:

```powershell
pio device monitor --port COM4 --baud 115200
```

Anche qui bisogna ottenere:

```text
READY hw-001
INFO board=lilygo-lora32-v1.6.1 chip=sx1276 ...
```

Poi chiudere il monitor.

---

## 10. Self-test software senza radio

Prima del test RF si può verificare il protocollo host:

```powershell
py hardware/lilygo-lora32-v1.6.1/host/bridge.py selftest
```

Il self-test HW-001 validato produce:

- PND1: 42 byte;
- PNF1: 60 byte;
- framing seriale TX: 88 byte;
- round-trip software: exact.

Questo test **non usa le antenne e non dimostra che LoRa funzioni**. Verifica soltanto encoding/decoding lato host.

---

## 11. Primo test LoRa reale A → B

Assicurarsi che:

- entrambe le antenne siano collegate;
- nessun monitor seriale stia usando COM3 o COM4;
- entrambe le schede siano accese;
- le schede siano separate fisicamente e non abbiano le antenne a contatto.

Eseguire:

```powershell
py hardware/lilygo-lora32-v1.6.1/host/bridge.py loopback --tx-port COM3 --rx-port COM4
```

Il programma trasmette automaticamente:

1. un PND1 reale;
2. lo stesso PND1 dentro un frame PNF1.

Per ciascuno controlla:

- byte ricevuti identici ai byte inviati;
- decodifica PND1 valida;
- decodifica PNF1 valida;
- RSSI;
- SNR.

Forma dell'output:

```json
{
  "pnd1": {
    "bytes": 42,
    "exact": true,
    "rssi_dbm": -40.0,
    "snr_db": 9.8
  },
  "pnf1": {
    "bytes": 60,
    "exact": true,
    "rssi_dbm": -40.0,
    "snr_db": 9.5
  },
  "success": true
}
```

---

## 12. Test inverso B → A

Per una validazione realmente bidirezionale:

```powershell
py hardware/lilygo-lora32-v1.6.1/host/bridge.py loopback --tx-port COM4 --rx-port COM3
```

HW-001 è considerato fisicamente completato solo quando entrambe le direzioni sono `success: true` e i frame risultano `exact: true`.

---

## 13. Risultato fisico di riferimento HW-001

Nel primo laboratorio validato:

### COM3 → COM4

- PND1 42 B: exact, RSSI -40 dBm, SNR 9.8 dB;
- PNF1 60 B: exact, RSSI -40 dBm, SNR 9.5 dB.

### COM4 → COM3

- PND1 42 B: exact, RSSI -37 dBm, SNR 9.5 dB;
- PNF1 60 B: exact, RSSI -36 dBm, SNR 9.8 dB.

Questi valori **non sono soglie universali**. Sono soltanto il risultato della specifica prova di banco.

---

## 14. Come interpretare RSSI e SNR

### RSSI

RSSI esprime la potenza del segnale ricevuto in dBm.

Esempio:

```text
-40 dBm
```

è un segnale molto più potente di:

```text
-100 dBm
```

Il numero più vicino a zero indica maggiore potenza ricevuta.

### SNR

SNR confronta segnale e rumore.

```text
SNR > 0 dB
```

significa che il segnale è sopra il rumore secondo quella misura.

Una caratteristica interessante di LoRa è che, a seconda della configurazione, può demodulare anche segnali estremamente deboli e in condizioni in cui l'SNR è negativo. Questo sarà studiato nei laboratori successivi.

---

## 15. Profilo radio congelato HW-001

```text
Frequenza       868.100 MHz
Bandwidth       125 kHz
Spreading       SF7
Coding rate     4/5
Sync word       0x12
Potenza TX      10 dBm
Preamble        8 simboli
Max payload     240 byte lato host
```

Questi valori appartengono all'adapter HW-001. **Non sono costanti del protocollo PollicinoNet.**

---

## 16. Problemi comuni e soluzioni

### `ModuleNotFoundError: No module named 'pollicino'`

Causa: il repository non è installato come package Python nell'ambiente usato da `py`.

Soluzione:

```powershell
py -m pip install -e . pyserial
```

Poi:

```powershell
py -c "import pollicino.net; print('OK')"
```

### `pio` non riconosciuto

Usare:

```powershell
py -m platformio ...
```

oppure controllare la directory Scripts dell'installazione Python.

### Porta COM occupata / `Access denied`

Probabilmente è ancora aperto:

- PlatformIO monitor;
- Arduino Serial Monitor;
- PuTTY;
- un'altra istanza del bridge.

Chiudere il programma che usa la porta e riprovare.

### Nessuna nuova COM compare

Controllare:

- cavo Micro-USB: deve essere **dati**, non solo alimentazione;
- driver USB-seriale;
- Gestione dispositivi;
- altra porta USB del PC.

### `FATAL radio-init=...`

Non procedere con i test RF. Verificare:

- revisione fisica della board;
- pinout;
- chip radio;
- firmware corretto;
- connessioni hardware.

### Timeout durante il loopback

Controllare nell'ordine:

1. antenne montate;
2. entrambe le board avviate;
3. nessun monitor seriale aperto;
4. COM corrette;
5. entrambe le board mostrano lo stesso profilo `INFO`;
6. distanza non eccessiva per il primo test;
7. ripetere con le board ferme.

---

## 17. Cosa deve consegnare lo studente

Per ogni coppia di schede:

1. screenshot o testo del `READY hw-001` di entrambe;
2. porte seriali assegnate;
3. output A → B;
4. output B → A;
5. tabella con byte, exact, RSSI e SNR;
6. breve spiegazione della differenza tra test host e test radio;
7. risposta: perché il numero della COM non identifica permanentemente la scheda?
8. risposta: perché chiudiamo il monitor seriale prima del loopback?
9. risposta: perché l'antenna va montata prima della trasmissione?
10. risposta: cosa dimostra `exact: true` e cosa invece non dimostra?

---

## 18. Esperimenti successivi

HW-001 risponde soltanto a questa domanda:

> Due schede fisiche possono trasportare PND1 e PNF1 invariati in entrambe le direzioni?

La risposta sperimentale è sì.

HW-002 dovrà studiare:

- molte trasmissioni, non due soltanto;
- packet loss;
- distribuzione di RSSI/SNR;
- diverse dimensioni di payload;
- latenza e airtime;
- distanza e ostacoli;
- confronto tra misura reale e simulatore PN-002;
- TRC fisico;
- in seguito SF, BW, coding rate e potenza TX.

---

## 19. Regola metodologica

Non confondere mai:

```text
COMPILA
  !=
BOOTTA
  !=
INIZIALIZZA LA RADIO
  !=
TRASMETTE
  !=
RICEVE
  !=
RICEVE ESATTAMENTE
  !=
FUNZIONA A LUNGA DISTANZA
  !=
È AFFIDABILE
```

Ogni affermazione richiede il proprio esperimento.

Questa separazione è uno dei principi centrali del percorso scientifico PollicinoNet.
