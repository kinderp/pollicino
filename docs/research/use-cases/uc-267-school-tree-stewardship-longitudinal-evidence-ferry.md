# UC-267 — Diario distribuito della cura degli alberi scolastici

**Stato:** proposta del 30 ottobre 2026; nessun albero, sensore o link fisico è stato misurato. Nessuna modifica al PHY LoRa congelato.

## Problema risolto

Per un alberello piantato nel cortile di una scuola, piantagione, verifiche successive, annaffiature, guasti del sensore e osservazioni mancanti sono eventi separati. Dopo mesi, diversi gruppi potrebbero non sapere **quali cure siano state realmente svolte**, se un'osservazione sia vecchia o se un "nessun problema" significhi in realtà "nessuna visita". Serve una storia verificabile e riunificabile anche tra siti con rete intermittente, senza trasformare gli studenti in soggetti tracciati.

## Attori e rete didattica messinese

Due aiuole o alberelli in **aree scolastiche autorizzate**, piccoli gruppi di osservatori, docente di Scienze, verificatore responsabile, eventuale sensore di umidità del suolo non obbligatorio, cache di sede, 4–8 schede LoRa degli studenti come relay/store-and-forward. Possibile estensione a iniziative civiche soltanto con autorizzazioni dei responsabili dei luoghi; non si presume una collaborazione comunale già esistente.

## Perché PollicinoNet e bearer

Le osservazioni sono brevi, sparse e utili anche se arrivano giorni dopo. La rete consegna **eventi append-only** referenziati a una pianta identificata con codice pubblico non personale, mentre le foto e i log restano locali finché non servono. La ricostruzione non deve assumere che ordine di ricezione = ordine degli eventi.

- **LoRa:** `tree_id` pseudonimo, `event_id`, classe evento, finestra/qualità del tempo, stato della revisione e hash dell'evidenza; dati piccoli solo se fattibili per l'adapter e budget.
- **BLE:** sincronizzazione locale in occasione di incontri.
- **Wi-Fi/Internet:** archivi, immagini senza persone, grafici, eventuali misurazioni complete.
- **USB/SD / trasporto fisico:** condivisione dell'archivio in assenza di accesso radio.
- `DISCOVERY`: aggiornamenti per alberello/sito autorizzato; `EXACT`: eventi e firme/digest; `SEMANTIC`: `CARE_RECORDED`, `OBSERVED_UNCERTAIN`, `INSPECTION_MISSED`, `REVIEWED`; non un verdetto automatico sulla salute della pianta.

## Test senza hardware

Simulare 12 mesi su 4 alberelli virtuali: piantagione, assegnazione di una visita, visita realmente eseguita, osservazione visiva non verificata, intervento autorizzato, omissione della visita, sensore invalido, annotazione duplicata e revisione successiva. Tre cache disconnesse ricevono eventi in ordine differente. Ricostruire una timeline usando ID unici, provenienza, tempi con incertezza e regole di revisione, **senza inventare un evento `WATERED` a partire da un piano `WATERING_SCHEDULED`**.

Output software: numero di visite effettivamente registrate, intervalli senza osservazione, segnalazioni da verificare e eventi contestati; non una percentuale di sopravvivenza dedotta da dati sintetici.

## Hardware e misure fisiche necessarie

Iniziare in laboratorio con piante fittizie e un sensore in vaso (facoltativo), poi due postazioni scolastiche reali autorizzate. Per qualche finestra un docente verifica di persona gli eventi annotati, mantenendo log di riferimento separati. Con 4–8 schede testare consegna di eventi in differita, duplicazioni e ricostruzione dopo blackout. Per analisi botaniche occorrono protocollo agronomico, strumenti adeguati e revisione esperta: una lettura di umidità **non dimostra** salute o fabbisogno di annaffiatura.

## Privacy, sicurezza e rischio operativo

Nessun nome di minore, volto, cronologia individuale, indirizzo di casa o posizione precisa di vegetazione sensibile. Solo siti istituzionali approvati, foto controllate senza metadati personali, retention breve dei log radio. Autenticare eventi e correzioni, separare segnalazione da intervento autorizzato, mantenere l'informazione di incertezza e impedire che una cache offline sovrascriva silenziosamente un evento discordante. Nessun sistema autonomo di irrigazione o trattamento; qualsiasi azione fisica resta alla responsabilità dei gestori.

**Difficoltà:** media per diario e simulatori, medio-alta con sensori e governance degli interventi.

## Differenza dai casi già esistenti

UC-003 è un trasporto generico di sensori rurali; UC-042 segue la custodia di beni; UC-113 gestisce il *ticket* di manutenzione di un sensore; UC-116 verifica un'osservazione naturalistica puntuale; UC-185 distingue non-rilevazione e assenza di osservazione; UC-234 misura visite agli orti. **UC-267 gestisce invece la storia plurimensile di un organismo/luogo con piano di cura, azione effettivamente svolta, verifiche e omissioni esplicite**. Non replica il singolo rilievo naturalistico.

## Gate di accettazione (futuri)

- `SCHEDULED`, `PERFORMED`, `MISSED`, `UNKNOWN` non vengono mai fusi automaticamente.
- Riordino, duplicazione, partizione e riavvio non eliminano la storia o i conflitti.
- Le azioni fisiche non possono essere attribuite al sistema senza evidenza e autorizzazione.
- Nessuna conclusione sanitaria o botanica, nessuna prestazione radio, senza misure reali e metodologia appropriata.
