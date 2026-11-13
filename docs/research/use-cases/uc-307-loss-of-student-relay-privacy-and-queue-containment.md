# UC-307 — Relay scolastico smarrito: contenere la perdita di dati e di consegne

**Stato al 13 novembre 2026:** proposta documentale, non implementata né testata. **Difficoltà:** alta. Solo livelli applicativi; nessuna modifica al PHY LoRa congelato, MAC, firmware o driver.

## Problema concreto
Una scheda prestata per una sperimentazione PollicinoNet viene smarrita o resa inaccessibile all'improvviso mentre custodisce capsule in attesa di un futuro incontro. Non possiamo chiedere al dispositivo di cancellarsi da remoto perché potrebbe restare disconnesso. Non possiamo neppure affermare che le consegne siano riuscite solo perché il nodo aveva preso in custodia gli oggetti.

**Domanda:** come limitare dati esposti e consegne sospese dopo la perdita improvvisa di un relay, distinguendo ciò che possiamo verificare da ciò che resta ignoto?

## Attori, nodi, scenario messinese
Quattro relay scolastici di prova, due cache/PC di laboratorio, un amministratore docente, mittente e destinatario di oggetti sintetici. Scenario logico: cache di Rometta, relay temporaneo, cache di Venetico; nessun collegamento fisico tra comuni viene presunto. In un secondo momento, relay degli studenti solo volontari; non si registrano tragitti o identità permanenti.

## Perché PollicinoNet
La custodia store-and-forward è una promessa **limitata**, non una garanzia di consegna. Un relay può trasportare ciphertext end-to-end senza diritto di leggerne il contenuto; quando sparisce servono altre copie o un retry, nuove credenziali per operazioni future e una diagnosi esplicita degli oggetti di cui non si conosce lo stato.

- **DISCOVERY:** avvisi brevi e autorizzati di epoca di fiducia/revoca; usare ID opachi non correlabili quando possibile.
- **EXACT:** hash/manifest di bundle di test, ricevute applicative indipendenti, evidenza di replica durevole e autorizzazione all'accesso.
- **SEMANTIC:** classificazione astratta del servizio e delle politiche di replica; non rivelare dati personali.

## Bearer ammessi
- **LoRa:** solo notifiche compatte di cambio stato e discovery, se già supportate dall'adapter e conformi al budget radio.
- **BLE:** riconciliazione con dispositivi vicini e scambio di ricevute.
- **Wi-Fi/LAN/Internet:** replica dei ciphertext, aggiornamento autorizzazioni e riconciliazione quando disponibili.
- **USB/SD o trasporto fisico:** trasferimento di pacchetti cifrati e log fra laboratori, su supporti approvati.
Nessuna promessa di cancellazione remota, di sicurezza fisica contro estrazione di chiavi dal microcontrollore o di blocco istantaneo delle credenziali offline.

## Esperimento software immediato — non eseguito
Simulare **6 nodi virtuali**, **24 bundle sintetici** e due classi di policy, usando lo stesso seed in tre bracci: relay sempre disponibile; relay perso senza replica; relay perso con replica preventiva autorizzata.
Introdurre iniezioni indipendenti: perdita prima/dopo l'accettazione di custodia, copia incompleta, ricevuta tardiva, riuso di token vecchio, nodo che resta offline dopo una revoca, collisione di ID effimeri e tentativo di consultare metadata non autorizzati.

Stati richiesti: **DELIVERED_VERIFIED**, **CUSTODY_ONLY**, **NEEDS_RETRY**, **POTENTIALLY_EXPOSED_METADATA**, **UNKNOWN**, **POLICY_REVOKED_WHEN_OBSERVED**.
Metriche software: numero di bundle ricostruibili da copie superstiti; falsi successi; superficie dei metadati esposti nel modello; richieste ammesse dopo/notificate prima della revoca; tempo virtuale al primo ripristino. Non chiamare questa simulazione “test di resistenza alla manomissione fisica”.

**Criteri di accettazione futuri:**
1. Mai convertire custodia in consegna senza verifica EXACT e ricevuta dell'app destinataria.
2. Nessun relay riceve plaintext o chiavi di decifrazione destinate ai destinatari; ispezionare il contenuto del proprio storage simulato.
3. Credenziali revocate diventano inutilizzabili sui nodi che **hanno ricevuto e verificato** la revoca; un nodo isolato può restare vulnerabile.
4. Senza copia superstite o log completo, stato **UNKNOWN/NEEDS_RETRY**, non successo né perdita dimostrata.
5. Lo stop alla partecipazione di un volontario e il consenso al trattamento dati rimangono prioritari.

## Prove hardware necessarie
Con **4–6 schede scolastiche** e due PC: preparare solo dati fittizi, mettere una scheda in modalità offline controllata (non smarrirla davvero), conservare l'immagine/log dello storage solo su supporto di laboratorio autorizzato, propagare un avviso di revoca alle altre e testare nuove richieste e riconciliazione da copie alternative.
Prima controllare capacità effettive di cifratura e gestione chiavi **senza assumere** secure element, secure erase o memoria anti-manomissione. Raccogliere ricevute e integrità; copertura, autonomia, tempi radio e PDR soltanto se misurati con strumenti e denominatori verificabili.

## Privacy, sicurezza e non obiettivi
Nessun dato reale degli studenti, posizioni di casa o contatti personali nelle capsule. Policy di minimizzazione, retention breve e procedure organizzative per dispositivo mancante. La cifratura lato destinatario protegge il contenuto solo nel modello di minaccia dichiarato: identificativi, dimensioni, tempi e copie già estratte possono restare esposti. Nessuna “remote wipe” garantita da una rete disconnessa. Ogni installazione reale richiede revisione della sicurezza.

## Non duplicazione
- **UC-201:** ritiro **volontario** e handoff controllato; qui il relay sparisce **senza preavviso**.
- **UC-019:** propagazione della revoca; qui la revoca è solo una parte della gestione delle code, delle copie e dell'esposizione.
- **UC-021:** trasporto a soglia di segreti; qui si valuta la protezione pratica di **qualunque relay perso** anche senza threshold.
- **UC-077/UC-253:** scadenza e custodia persistente; non coprono da soli l'incidente fisico improvviso con stato ignoto.
- **UC-206:** readiness del dispositivo prima del servizio, non conseguenze di una scomparsa.

## Fonti metodologiche
- NIST IR 8259 Rev. 1 (aprile 2026), cybersecurity di prodotti IoT: https://csrc.nist.gov/pubs/ir/8259/r1/final
- NIST IoT Device Cybersecurity Requirement Catalog, data protection: https://pages.nist.gov/IoT-Device-Cybersecurity-Requirement-Catalogs/technical/
- RFC 9171 per contesto DTN, **non dichiarazione di conformità PollicinoNet BPv7**: https://www.rfc-editor.org/rfc/rfc9171.html
