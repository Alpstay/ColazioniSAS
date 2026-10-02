# Aggiornamento quotidiano dell'elenco ospiti (La Scatola → app colazioni)

Procedura per l'attività pianificata che ogni mattina aggiorna `roster.json` e il roster
incorporato in `index.html`. La **password Sala** per cifrare i nomi NON è in questo
repository (è pubblico): viene data nel testo dell'attività pianificata.

## Regole

- Gli ID ricevuti da Slope / La Scatola non si modificano mai: si copiano identici.
- Nomi e altri dati personali degli ospiti non si stampano, non si riassumono e non si
  scrivono in nessun file del repository. Vivono solo in file privati nella cartella di
  lavoro temporanea (scratchpad) e, cifrati, dentro `names_enc`.
- Di `index.html` si riscrive solo il blocco tra `/*ROSTER_EMBED_START*/` e
  `/*ROSTER_EMBED_END*/`, con `tools/incorpora_roster.py`. Nient'altro.
- Se La Scatola non risponde, dà zero stanze, o `tools/verifica.py` fallisce: **non
  pubblicare**. L'app online ha già l'elenco dei due giorni successivi all'ultimo
  aggiornamento; meglio un elenco di ieri che uno sbagliato.

## Dati

- Struttura: Alpstay – Smart Hotel Saslong, `property_id` `33333333-3333-4333-8333-333333333333`.
- `G` = oggi nel fuso Europe/Rome (AAAA-MM-GG). `G-1` = ieri, `G+1`, `G+2` = i due giorni dopo.
- La colazione di `G` è di chi ha dormito la notte `G-1`: prenotazioni con `arrival < G <= departure`.

## Passi

1. **Freschezza**: `get_freshness`. Se `lodging_reservation` del Saslong non si aggiorna da
   più di 6 ore, prosegui ma dillo nel riepilogo finale.
2. **Prenotazioni** (viste senza dati personali):
   - `list_in_house` con `date = G-1`, `property_id`, `limit 500` → chi fa colazione oggi.
   - `list_arrivals` con `date = G` e poi con `date = G+1` → arrivi per le previsioni di `G+1` e `G+2`.
   - Segui `next_cursor` finché non è nullo; controlla che `page.returned` sommi a `page.total`.
3. **`stays.json`** nello scratchpad: un oggetto per prenotazione, senza duplicati di `reservation_id`:
   `{"room": room_name, "people": adults + children, "arrival": ..., "departure": ..., "reservation_id": ...}`.
   Includi anche le prenotazioni senza camera (`"room": null`): lo script le salta ma le
   riconosce. Escludi quelle con `is_option: true`.
4. **Ospiti registrati** (vista con dati personali, da non mostrare):
   `query_curated_view` su `curated_guest_stays` con filtri
   `property_id eq <Saslong>`, `stay_start lt G`, `stay_end gte G`, `limit 500`.
   I risultati sono grandi e vengono salvati su file dal sistema: usa quei file così come
   sono. Segui `next_cursor` (stessi filtri) finché non è nullo. Se una pagina arriva nel
   messaggio invece che su file, salvala tu in un file `{"rows":[...]}` nello scratchpad
   tenendo solo i campi `reservation_id, is_primary_guest, first_name, last_name, language,
   citizenship, order_customer_first_name, order_customer_last_name, order_customer_language`.
5. **Costruisci**: dalla cartella del repository
   `python3 tools/build_roster.py <stays.json> <file1,file2,...> "<PASSWORD SALA>" G G+1 G+2 > roster.json`
   Leggi il resoconto su stderr: il numero di stanze di `G` deve coincidere con le
   prenotazioni con camera di `list_in_house`. Una riga `ATTENZIONE` indica quasi sempre un
   `reservation_id` trascritto male in `stays.json`: correggilo e rilancia.
6. **Incorpora**: `python3 tools/incorpora_roster.py index.html roster.json`
7. **Verifica**: `python3 tools/verifica.py index.html roster.json G <file1,file2,...>` deve finire con `verifica OK`.
8. **Pubblica**: `git add index.html roster.json`, un commit `Elenco ospiti colazione G`,
   `git push origin HEAD:main`. Se il push è rifiutato, non insistere: riportalo nel riepilogo.
9. **Riepilogo** in italiano, senza nomi: stanze, persone, partenze e fermate di oggi;
   eventuali stanze senza ospite registrato (solo i numeri di stanza) e prenotazioni senza camera.

## Lingua del saluto

La decide `tools/build_roster.py`: vale il campo lingua dell'ospite registrato principale se
diverso da `it` (in Slope `it` è il valore predefinito, quindi non dice nulla); altrimenti
la cittadinanza (IT → italiano, DE/AT/CH → tedesco, FR → francese, CN/TW → cinese, …; paesi
plurilingue o non previsti → inglese). Senza ospite registrato la lingua resta vuota e il
chiosco usa il saluto a rotazione.
