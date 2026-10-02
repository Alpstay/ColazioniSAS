"""Controlli prima di pubblicare. Esce con errore se qualcosa non va.
Uso: python3 tools/verifica.py index.html roster.json AAAA-MM-GG guests1.txt[,guests2.txt...]

1. roster.json contiene il giorno indicato, con almeno una stanza
2. l'HTML incorpora lo stesso roster
3. il JavaScript dell'HTML è sintatticamente valido (node --check)
4. nessun cognome o nome degli ospiti compare in chiaro nei dati pubblicati
"""
import json, re, subprocess, sys, tempfile

html_p, roster_p, giorno, guests = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
html = open(html_p, encoding="utf-8").read()
roster_txt = open(roster_p, encoding="utf-8").read()
roster = json.loads(roster_txt)

day = roster.get("days", {}).get(giorno)
assert day and day.get("rooms"), "roster.json non contiene stanze per " + giorno
assert all(isinstance(v.get("max"), int) and v["max"] > 0 for v in day["rooms"].values()), "persone per stanza non valide"

m = re.search(r"/\*ROSTER_EMBED_START\*/const ROSTER_EMBEDDED = (.*?);/\*ROSTER_EMBED_END\*/", html, re.S)
assert m, "blocco ROSTER_EMBED non trovato in index.html"
emb = json.loads(m.group(1).replace("<\\/", "</"))
assert emb.get("generated") == roster.get("generated") and emb["days"][giorno]["rooms"] == day["rooms"], \
    "il roster incorporato nell'HTML non coincide con roster.json"

js = re.search(r'<script type="module">(.*?)</script>', html, re.S).group(1)
with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as f:
    f.write(js)
subprocess.run(["node", "--check", f.name], check=True)

rows = []
for g in guests.split(","):
    j = json.load(open(g, encoding="utf-8"))
    rows += j.get("rows") or j.get("data") or []
parole = set()
for r in rows:
    for k in ("last_name", "first_name", "order_customer_last_name", "order_customer_first_name",
              "primary_guest_last_name", "primary_guest_first_name"):
        for w in re.split(r"[\s,]+", r.get(k) or ""):
            if len(w) >= 5:
                parole.add(w.lower())
# si controllano solo i dati (roster.json e blocco incorporato): il resto dell'HTML è interfaccia fissa
pubblico = (m.group(1) + roster_txt).lower()
trovate = sorted(w for w in parole if re.search(r"(?<![a-zà-ÿ0-9+/])" + re.escape(w) + r"(?![a-zà-ÿ0-9+/=])", pubblico))
assert not trovate, "possibili nomi in chiaro nei file pubblici: %d parole (non pubblicare)" % len(trovate)

print("verifica OK: %s, %d stanze, %d parole-nome controllate, nessuna in chiaro" % (giorno, len(day["rooms"]), len(parole)))
