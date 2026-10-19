# UC-226 — Coordinamento dell'airtime fra campagne scolastiche

**Problema:** due gruppi LoRa organizzano prove sovrapposte e falsano le misure reciproche. Servono un calendario firmato e un resoconto separato delle trasmissioni realmente eseguite.

**Scenario:** due laboratori fra Villafranca e Venetico, 6–10 schede e due ricevitori indipendenti. PollicinoNet trasferisce manifest e aggiornamenti store-and-forward.

**Bearer:** LoRa per ID e piani compatti; BLE per configurazione; Wi-Fi/Internet per log; SD/USB o trasporto fisico per prove complete.

**Software:** simulare finestre sovrapposte, cancellazioni tardive e clock incerti. Confrontare conflitti previsti e osservazioni; una prenotazione non garantisce accesso radio.

**Hardware:** prove autorizzate con TX/RX loggati, orari e airtime misurati; PHY/MAC invariati.

**Sicurezza e privacy:** solo identificativi di campagna, niente percorsi di studenti; aggiornamenti autenticati. Non equivale a certificazione normativa.

**Difficoltà:** medio-alta. Diverso da UC-063 (monitoraggio RF), UC-097 (piani di test) e UC-128 (prenotazione di contatti): isola esperimenti concorrenti.
