# UC-252 — Giornata di servizio volontario: autonomia e consegne utili del relay nello zaino

**Stato:** proposta sperimentale del 25 ottobre 2026; nessuna prova software/fisica eseguita. **Difficoltà:** media per il simulatore, medio-alta per un esperimento energetico controllato.

## Problema e storia d'uso
Una scheda passa il collaudo sul banco ma, quando è utilizzata per diverse ore in uno zaino, potrebbe consumare troppa energia, riempire le code o non contribuire ad alcuna consegna utile. Misurare solo «quanti pacchetti trasmette» non risponde alla domanda: **quanto costa, in energia e partecipazione volontaria, una vera giornata di servizio store-and-forward?**

**User story:** «Come docente, voglio confrontare due politiche applicative di disponibilità del relay e scegliere quella con il miglior equilibrio fra consegne verificate, autonomia e diritto dello studente a interrompere il test».

## Attori e nodi
4–8 schede commissionate, studenti partecipanti volontari, docente responsabile, due ricevitori indipendenti, stazioni scolastiche statiche e logger energetico. Primo studio su banco e in perimetro autorizzato; solo dopo eventuali incontri fra checkpoint scolastici di Messina, Villafranca, Rometta e Venetico. **I nodi non registrano percorsi individuali**.

## Perché PollicinoNet e bearer
LoRa porta pochi oggetti di test e ricevute compatte; BLE è un possibile canale diagnostico locale; Wi-Fi/Internet scarica log e payload più grandi presso i checkpoint; USB/trasporto fisico riporta i log quando le reti sono scollegate. La sfida è proprio l'incontro opportunistico fra nodi mobili e fissi, con conservazione locale dei messaggi. Il PHY LoRa congelato non cambia; il confronto riguarda esclusivamente politiche applicative e configurazioni ammesse dal sistema esistente.

## Esperimento software subito
Simulare 8 relay, due checkpoint, una giornata fittizia di finestre di contatto, batteria/energia sintetiche, generazione di messaggi e due policy: (A) relay sempre disponibile entro i limiti ammessi; (B) disponibilità in finestre predefinite con budget e pausa locale immediata. Aggiungere batterie scariche, riavvii, contatti brevissimi, code sature, duplicati e interruzione volontaria anche senza connessione Internet.

Verificare invarianti: `STOP` locale blocca nuovi inoltri dell'esperimento senza dipendere dal gateway; un messaggio conta come consegnato solo dopo la verifica applicativa (UC-221); energia simulata e reale non vengono confuse; le finestre di disponibilità non rivelano orari di uscita/arrivo personali.

Metriche: oggetti unici accettati, byte utili, attese, energia stimata per oggetto accettato (solo in simulazione), copie duplicate, giorni/ore di disponibilità esplicitamente autorizzate, motivo di esclusione dei dati non osservabili.

## Prove hardware e procedura
1. Commissionare le schede secondo UC-206; controllare alimentazione, antenne e log.
2. Banco alimentato da strumenti adatti: misurare corrente/energia su tempi controllati in stato inattivo, ricezione e test applicativi, senza assumere il consumo dalla scheda tecnica.
3. Eseguire un test incrociato in luogo autorizzato: stessi dispositivi e carico, policy A/B in ordine alternato. Tenere separati ambiente, temperatura, orientamento e condizioni della batteria.
4. Solo dopo, trial volontario fra **checkpoint pubblici concordati**, con logger locali e ricevitori indipendenti; sincronizzare il recupero dei log senza tracciare spostamenti di singoli studenti.
5. Confrontare energia reale, ricevute applicative effettive, TX/RX, tempo di contatto e percentuale di prove incomplete. **Nessun numero atteso di copertura o autonomia viene anticipato**.

Usare involucri e batterie commerciali sicuri, niente cablaggi improvvisati o batterie portate da studenti senza valutazione dei rischi. Rispettare limiti normativi radio, supervisione e privacy.

## Privacy e sicurezza
Partecipazione informata, opt-in e STOP offline (UC-217), raccolta minima di misure sul dispositivo e su checkpoint, ID temporanei, nessun GPS, nessun log nominale di orari o tragitti, nessun incentivo a effettuare deviazioni o ad aumentare attività radio. Registrare eventi energetici e ricevute tramite ID di prova. Ritiro immediato del dispositivo in caso di problemi elettrici/meccanici.

## Distinzione dai casi esistenti
UC-206 certifica lo stato **iniziale**; UC-211 studia la posizione dell'antenna; UC-217 governa il consenso; UC-231 registra il budget di TX; UC-095 tutela risorse dei volontari; UC-174 propone finestre di rendezvous. **UC-252 è un confronto sperimentale completo della fattibilità di una *giornata di servizio* in termini di energia effettivamente misurata per consegna utile, con policy incrociate e arresto locale.** Non modifica PHY/MAC/driver.
