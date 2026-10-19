# UC-228 — Audit del bias di campionamento dovuto alla rete

## Problema
Le postazioni più connesse inviano più campioni: le statistiche basate solo sui messaggi ricevuti possono risultare distorte.

## Scenario
Due sensori fissi autorizzati nell'area di Messina, 6–12 relay scolastici e un collector. Nessun tracciamento degli studenti.

## PollicinoNet e trasporti
LoRa porta conteggi e hash; BLE o Wi-Fi trasporta serie di dati; Internet oppure USB/SD raccoglie dataset completi. Lo store-and-forward preserva il conteggio delle osservazioni generate anche quando arrivano tardi.

## Esperimento software
Generare dati sintetici con diverse probabilità di consegna. Confrontare la media dei soli ricevuti con la verità simulata. Testare campioni mancanti, log incompleti e correzioni basate su probabilità di inclusione esplicitamente note. Non dichiarare imparzialità se le ipotesi non sono giustificate.

## Prova hardware
6–12 schede, due checkpoint e sensori che registrano localmente. Confrontare misure prodotte, ricevute e riconciliate. Raccogliere tempi e trasferimenti veri.

## Sicurezza e difficoltà
Aggregati per sito, firme, nessuna graduatoria degli studenti; difficoltà alta per la statistica. Diverso da UC-178 (log mancanti), UC-185 (non-rilevazioni) e UC-224 (previsioni di incontro): misura il bias del risultato finale.
