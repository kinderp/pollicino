# UC-234 — Osservatorio didattico delle visite agli orti scolastici

**Stato:** proposta documentale del 20 ottobre 2026; nessun dato biologico o radio misurato.

## Problema
Due orti o aiuole scolastiche hanno connessioni intermittenti. I conteggi di passaggi di insetti non sono confrontabili se un sensore funziona per un'ora e un altro per dieci minuti, o se un evento viene contato più volte. Vogliamo studiare la raccolta di **visite candidate**, senza pretendere di identificare automaticamente specie o popolazioni.

## Attori e scenario Messina
Due postazioni fisse autorizzate, per esempio Rometta e Venetico, docenti di scienze e informatica, due contatori manuali o ottici non invasivi e 4–6 schede degli studenti come relay. Nessun tracciamento di persone o luoghi sensibili.

## Perché PollicinoNet; bearer
LoRa porta conteggi brevi, finestra di osservazione, durata valida e hash di eventuali evidenze. BLE per configurazione; Wi-Fi/Internet o USB/SD per registri e grafici. Il trasporto store-and-forward preserva gli intervalli osservati, mancanti e recuperati dopo una disconnessione.

## Test software immediato
Generare eventi artificiali, falsi passaggi, duplicati, ore di inattività, orologi imprecisi e intervalli non comparabili. Produrre **eventi candidati per durata effettivamente osservata**, indicando `VALID`, `UNCERTAIN` o `MISSING`; mai trasformare automaticamente un sensore non funzionante in zero visite.

## Prova fisica necessaria
Due postazioni e 4–6 schede LoRa; usare contatori non invasivi oppure osservazione manuale. Per un sottoinsieme di finestre confrontare conteggi del sensore e annotazioni di riferimento fatte dai docenti. Registrare affidabilità dei sensori e completezza delle consegne con dati effettivi. Evitare qualsiasi conclusione ecologica non supportata.

## Privacy, sicurezza, difficoltà
Preferire nessun microfono e nessuna telecamera, proteggere l'ubicazione di eventuali osservazioni sensibili e utilizzare soltanto postazioni approvate. Difficoltà **media**. Non modificare il PHY LoRa.

## Originalità
UC-003 è trasporto rurale generico, UC-116 è osservazione verificata, UC-185 è non-rilevazione e UC-223 è confronto sole/ombra. **UC-234 aggiunge un protocollo educativo di conteggio di visite candidate con sforzo di osservazione e incertezza espliciti**.
