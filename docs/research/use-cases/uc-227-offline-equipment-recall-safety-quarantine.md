# UC-227 — Richiamo offline dei lotti di dispositivi

**Problema:** una scuola identifica un lotto sospetto di schede o accessori distribuiti a laboratori disconnessi. La rete deve propagare il richiamo, senza confondere avviso ricevuto, ritiro fisico e autorizzazione al riuso.

**Scenario:** tecnico scolastico, docente, 4–8 schede etichettate con lotti inventati, due laboratori fra Messina e Venetico e relay mobili. Nessun componente realmente difettoso nei test.

**Perché PollicinoNet:** conserva gli avvisi firmati durante le partizioni e li inoltra al successivo contatto.

**Bearer:** LoRa per lotto, versione e STOP_USE; BLE per verifica al banco; Wi-Fi/Internet per verbali; trasporto fisico per restituire gli oggetti.

**Test software:** messaggi fuori ordine, firme non valide, lotti diversi e revoche tardive. Uno stato CLEARED vecchio non deve cancellare un richiamo più recente. Distinguere NOTIFIED, ACKNOWLEDGED, RETURNED, INSPECTED e CLEARED.

**Test fisico:** 4–8 schede e due postazioni; ritardare intenzionalmente un avviso e verificare gli stati locali, poi il ritiro dimostrativo. Misurare tempi veri, non stimarli.

**Privacy e sicurezza:** IDs dei lotti e non delle persone, accessi per ruolo e firme; in caso di difetto reale applicare subito le procedure della scuola, senza affidarsi alla rete.

**Difficoltà:** media. UC-039 riguarda vulnerabilità software; UC-113 la manutenzione; UC-201 la dismissione. Qui la novità è il richiamo verificabile di un lotto fisico.
