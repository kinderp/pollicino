# UC-315 — DNA: prestito di strumenti fra laboratori con idoneità di misura

**Stato:** proposta documentale. **Difficoltà:** alta (governance/validità scientifica), media per prototipo software. **Dominio:** DNA, risorse condivise, metrologia scolastica.

## Problema
Una classe ha bisogno di uno strumento (es. multimetro, luxmetro o sensore di riferimento) per una misura comparativa. Una scuola vicina dichiara di possederlo, ma **"disponibile" non significa "adatto"**: lo strumento può essere fuori calibrazione, non coprire il campo di misura o avere un problema documentato. DNA deve proporre un prestito **condizionato da prove**, non trasformare un annuncio in certificazione.

## Scenario nel Messinese
Un laboratorio scolastico a Milazzo richiede un luxmetro per confrontare campioni. Un altro istituto a Venetico dichiara uno strumento; un terzo a Rometta può offrire un controllo incrociato. Il sistema DNA collega richiesta, intervallo operativo, precisione desiderata, scheda tecnica/rapporto di verifica, autorizzazione prestito e disponibilità temporale. Relay scolastici e schede trasportate volontariamente trasferiscono metadati e richieste in store-and-forward; lo strumento è spostato fisicamente soltanto da persone autorizzate. **Nessun collegamento radio fra comuni è presupposto.**

## Attori e bearer
- Richiedente/docente, responsabile del laboratorio proprietario, eventuale referente metrologico, custodi di cache e relay, revisore della misura.
- **LoRa:** richiesta compatta, hash del rapporto, stato d'idoneità e accettazione; **BLE:** check in/out in laboratorio; **Wi-Fi/Internet/USB:** manuale, rapporto, foto dello strumento; **trasporto fisico:** strumento con consegna supervisionata.
- DNA presenta una spiegazione `WHY / WHY_NOT / UNKNOWN` ancorata alle prove esatte; nessuna inferenza da nomi generici di prodotto.

## Modello minimo
`request_id`, `required_quantity`, `range`, `accuracy_requirement`, `conditions`, `instrument_pseudonym`, `instrument_model`, `serial_local_only`, `verification_document_hash`, `verification_date`, `verification_scope`, `expiry_policy`, `known_fault`, `loan_approval`, `qualification_state` (ELIGIBLE_FOR_SUPERVISED_REVIEW / INELIGIBLE / UNKNOWN), `application_receipt`. Una qualifica positiva richiede evidenze sufficienti *per quello specifico uso e momento*, non una generica etichetta "calibrato". Se le condizioni e l'incertezza non sono documentate, lo stato è UNKNOWN.

Il NIST ricorda che possedere uno strumento calibrato non rende automaticamente riferibile qualsiasi misura: occorre documentare metodo, catena di calibrazioni, incertezza e condizione di utilizzo. Nella scuola è un riferimento metodologico, non un'attestazione NIST: https://www.nist.gov/metrology/metrological-traceability

## Software immediato — non eseguito
Creare 4 richieste e 12 strumenti **completamente inventati**; introdurre rapporti scaduti, range non compatibili, metadati mancanti, prenotazioni sovrapposte, autorizzazioni revocate, prove arrivate dopo una proposta DNA. Simulare 3 cache con ordini diversi di consegna. Valutare risultati DNA con motivazione e provenance, evitando che nuovi dati vecchi sovrascrivano una non idoneità.

**Criteri di accettazione:**
1. Incompatibilità accertata → INELIGIBLE anche se lo strumento è disponibile;
2. rapporto assente o scadenza inconoscibile → UNKNOWN, mai promozione silenziosa;
3. revoca o difetto successivo invalidano la proposta, anche se il messaggio arriva in ritardo;
4. prestito non diventa completato senza conferma umana della consegna fisica;
5. seriali personali o dettagli localizzabili non sono trasmessi in capsule pubbliche;
6. nessuna misura prodotta è dichiarata riferibile o certificata senza una vera catena documentale.

## Prove hardware e fisiche — non eseguite
Prima 4 schede LoRa e 2 PC; simulare solo cataloghi e documenti artificiali. Poi un luxmetro scolastico, un protocollo controllato di confronto, verifica manuale da responsabili e ricevute sulle due scuole se autorizzate. Non spedire strumenti fragili o componenti pericolosi con minori in assenza di autorizzazioni. Separare esito del trasporto dati, verifiche metrologiche e conclusioni dell'esperimento.

## Sicurezza/privacy
Minimizzazione e ACL sulle schede degli strumenti, hash per versionare rapporti, firme e log d'approvazione dei docenti; tenere numero di serie/custodi in archivio scolastico protetto. Non trasportare dati di studenti o inventari dettagliati su broadcast. Non usare il sistema per strumenti clinici, verifiche di sicurezza o certificazioni ufficiali.

## Anti-duplicazione
- **UC-015/194:** inventari e prenotazioni, non l'idoneità per una **misurazione specificata**.
- **UC-293:** geometria/elettronica di ricambi Romeo, non catena di prova, range/incertezza di strumenti di misura.
- **UC-031/166:** dati di calibrazione e confronto tra sensori; qui DNA usa quelle evidenze come **gate di matching fra scuole** e prestito.
- **UC-244/270/272:** inferenze DNA e loro spiegazione/temporalità; qui sono applicate al vincolo di idoneità metrologica.

**Confini:** proposta, nessun prestito o esperimento reale, nessuna certificazione, nessuna modifica al PHY LoRa.
