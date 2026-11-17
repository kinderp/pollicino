# UC-316 — Museo diffuso offline: itinerari culturali con fonti e diritti verificabili

**Stato:** proposta documentale (non implementata). **Priorità:** alta per FSL e collaborazione fra scuole del Messinese. **Difficoltà:** medio-alta; alta se si includono collezioni reali e autorizzazioni. **Dominio:** Raiatea, cultura, P2P, servizi territoriali offline.

## Problema risolto e novità
Un visitatore di un percorso culturale scolastico trova un cartello o un QR, ma non ha Internet. Anche se un testo o una registrazione è presente su una cache vicina, non è detto che sia aggiornato, corredato di una fonte verificabile, riproducibile nella lingua desiderata o distribuibile per diritto d'autore. Proponiamo **micro-guide versionate e verificabili, associate a punti culturali pubblici senza identificare i visitatori**. L'identità del contenuto e i suoi permessi restano distinti dalla semplice scoperta della tappa. Le narrazioni AI sono bozze, mai fonti storiche autonome.

## Scenario provincia di Messina
Un percorso didattico *interamente fittizio* presenta 4 tappe generiche fra laboratorio scolastico a Milazzo, postazione a Rometta, una postazione a Saponara e un checkpoint dimostrativo a Venetico. Le tappe reali, i diritti sui materiali e i responsabili sono ancora da definire: non attribuire ad alcun monumento una storia inventata. Una scuola prepara e revisiona schede con fonti; altre cache ricevono i manifest con relay LoRa portati volontariamente durante spostamenti ordinari. A ogni tappa una PWA locale o un QR pubblico mostra contenuti autorizzati, se realmente presenti in cache. La rete non registra il percorso dei visitatori.

## Attori, nodi e bearer
- Docenti/curatori, revisore della fonte, eventuale titolare dei diritti, 3 cache scolastiche, checkpoint LoRa, relay studenti volontari e visitatore anonimo.
- **LoRa:** annuncio compatto di `exhibit_id`, versione, hash del manifest e stato di aggiornamento o ritiro, quando la capacità del bearer lo consente; niente audio/foto massivi e nessuna pretesa di geolocalizzazione.
- **BLE:** discovery locale facoltativa e piccoli metadati, soltanto se l'hardware la supporta.
- **Wi-Fi/LAN/Internet:** PWA locale, HTML accessibile, immagini e audio autorizzati; può non esserci Internet.
- **QR su carta e USB/SD/trasporto fisico:** accesso locale e movimentazione di pacchetti grandi con verifica EXACT; i QR non danno prova che una persona sia sul posto.
- Contratti DISCOVERY, EXACT e SEMANTIC rimangono separati dai bearer.

## Informazioni minime e policy
`exhibit_id`, `manifest_version`, `source_ids`, `source_version_hashes`, `claim_review_state`, `text_language`, `accessibility_variant`, `content_hash`, `license_id`, `rights_scope`, `consent_status` se pertinente, `publish_approval`, `withdrawal_epoch`, `cache_receipt`, `content_freshness_state`.
Stati minimi: PROPOSED, REVIEWED, RELEASED, WITHDRAWN, UNKNOWN_LICENSE. `RELEASED` richiede approvazione umana e diritti congruenti per ogni file derivato. La revoca propagata in ritardo non garantisce cancellazione istantanea di copie già diffuse: indicare tale limite e impedire nuove esposizioni conosciute come revocate. Separare metadati pubblici di tappa dai log amministrativi riservati. Evitare analytics di posizione e indirizzi personali.

## Prova software immediata — progettata, NON eseguita
Creare 12 schede inventate, 3 lingue/varianti accessibili, 3 cache virtuali e una sequenza deterministica di 40 eventi: pubblicazioni, consegne duplicate, revisioni tardive, cambio hash della fonte, materiale senza licenza, ritiro e download richiesto offline. Simulare ritardi e differenti ordini di arrivo; la PWA può mostrare solo il contenuto che la cache ha verificato, non l'oggetto appena annunciato.

**Criteri di accettazione:**
1. Una guida priva di diritto di distribuzione o revisione non diventa pubblica.
2. Un annuncio DISCOVERY non viene spacciato per disponibilità di audio/immagine integrale.
3. Citazioni Raiatea rimangono ancorate a versione e hash delle fonti: una nuova edizione richiede riesame.
4. Un ritiro conosciuto blocca le nuove esposizioni, ma il report dichiara esplicitamente le copie offline non raggiunte.
5. La variante testuale resta accessibile se non è disponibile l'audio, senza inventare traduzioni o contenuti.
6. Nessun evento di prova contiene visite individuali o GPS di studenti.

## Hardware e prova provinciale — non eseguite
Prima 4 schede LoRa, 2 PC, un punto Wi-Fi di laboratorio autorizzato e 3 cache simulate; trasferire solo manifest sintetici LoRa e una scheda HTML di prova via Wi-Fi/USB. Registrare TX osservate, RX e ricevute applicative senza dedurre copertura intercomunale. Solo dopo una sperimentazione autorizzata proporre una tappa fisica con QR e materiale con licenze idonee. I relay sono volontari e non tracciati; nessuna installazione su monumenti senza accordo.

## Privacy, sicurezza, limiti
Nessun conteggio di visitatori identificabili, niente percorsi, né memorizzazione di query personali per default. Autenticare il curatore e firmare i manifest; PWA sanitizzata contro script/iniezioni nei testi recuperati; controllare licenze e diritti di immagini, audio, traduzioni e riproduzioni. Non generare né pubblicare descrizioni storiche prive di fonti.

## Anti-duplicazione
- **UC-041/142:** cache e mailbox locali generiche; qui l'esperienza pubblica di **percorso culturale accessibile** richiede schede per tappa, policy dei diritti e revisione editoriale.
- **UC-006/096/296:** documenti Raiatea e citazioni; qui si tratta di **pubblicazione multimediale multilingue**, rights gate e ritiro nel punto di fruizione.
- **UC-192/288:** derivati didattici accessibili/tradotti; qui varianti culturali con revisione del curatore e possibilità di fruizione anonima offline.
- **UC-236/295:** room territoriali e guest post, non una guida culturale verificabile senza interazione sociale.
- **UC-312:** archivio di memorie orali e consensi degli intervistati, non un museo diffuso con tappe e diritti di ogni contenuto esposto.

## Fonti metodologiche
- Commissione europea (27 ottobre 2025), guida pratica al copyright museale: https://digital-strategy.ec.europa.eu/en/miscellaneous/step-step-guide-copyright-museums
- ICOM, copyright e riproduzioni del patrimonio: https://icom.museum/en/heritage-protection/copyright/

**Confini:** nessun percorso reale pubblicato, nessun dataset o risorsa di terzi caricata, nessun risultato fisico, nessuna modifica a PHY LoRa congelato/MAC/driver/firmware.
