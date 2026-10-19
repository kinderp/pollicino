# UC-230 — Conformità delle capsule su bearer diversi

## Problema
Lo stesso messaggio arriva via LoRa, BLE, Wi-Fi, QR, NFC, audio oppure USB. Un adapter non deve modificare identità, integrità, permessi o scadenza, né duplicare un'azione.

## Attori e scenario Messina
Due laboratori scolastici, 4–6 schede LoRa, due PC e telefoni; relay mobili volontari fra checkpoint autorizzati. Dati sintetici.

## Perché PollicinoNet e bearer
Store-and-forward consente più percorsi. LoRa porta capsule compatte; BLE/Wi-Fi payload; QR/NFC/audio messaggi piccoli; USB/SSD trasporto fisico; Internet opzionale.

## Test software
Envelope fittizio firmato con ID, hash e policy. Provare ordine inverso, duplicazione, firme non valide, troncamenti e cambio di bearer. Matrice PASS/FAIL/NOT_TESTED: identità invariata, firma valida, permessi rispettati, una sola accettazione applicativa.

## Prova reale
Due percorsi differenti per lo stesso oggetto, 4–6 schede e telefoni. Raccogliere conferme indipendenti, byte verificati e ritardi reali; nessuna conclusione RF da simulazioni.

## Privacy, sicurezza e difficoltà
Chiavi di test, nessuna identità personale, parsing con limiti e anti-replay. Difficoltà medio-alta.

## Originalità
UC-124 sceglie il bearer, UC-175 controlla duplicati, UC-203/213/220 introducono i trasporti e UC-221 conferma l'accettazione. Questo caso controlla l'equivalenza semantica *tra* adapter.
