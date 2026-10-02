"""Costruisce roster.json (uno o più giorni di colazione) per l'app Colazioni Saslong.

Ingressi (file privati, MAI da pubblicare):
  stays.json  -> lista prenotazioni: [{"room","people","arrival","departure","reservation_id"}]
  guests.json -> {"rows":[...]} righe di curated_guest_stays (La Scatola)
Uso:
  python3 build_roster.py stays.json guests.json PASSWORD 2026-10-02 [2026-10-03 ...] > roster.json

Colazione del giorno D = chi ha dormito la notte D-1: arrival < D <= departure.
"dep": true = stanza in partenza quel giorno; false = fermata.
Gli ID di Slope non vengono mai modificati: servono solo per unire prenotazioni e ospiti.
"""
import base64, collections, datetime, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SUPPORTED = {"it", "de", "en", "fr", "es", "nl", "pt", "pl", "cs", "ru", "zh", "ko", "ar", "he"}
# cittadinanza -> lingua del saluto. Paesi plurilingue o non coperti -> inglese.
COUNTRY = {}
for lang, codes in {
    "it": "IT SM VA", "de": "DE AT LI CH", "fr": "FR MC", "nl": "NL",
    "es": "ES MX AR CO CL PE UY VE EC BO PY CR PA DO GT HN SV NI CU",
    "pt": "PT BR", "pl": "PL", "cs": "CZ", "ru": "RU BY KZ",
    "zh": "CN TW HK MO", "ko": "KR", "he": "IL",
    "ar": "SA AE EG QA KW BH OM JO LB MA DZ TN IQ SY LY YE",
}.items():
    for c in codes.split():
        COUNTRY[c] = lang
ITER = 250_000
b64 = lambda b: base64.b64encode(b).decode()


def lingua(guest):
    """Lingua dell'ospite registrato. In Slope il campo lingua resta spesso 'it' di default:
    vale solo se diverso da 'it'; altrimenti decide la cittadinanza."""
    if not guest:
        return None
    g = (guest.get("language") or "").lower()
    if g in SUPPORTED and g != "it":
        return g
    cit = (guest.get("citizenship") or "").upper()
    if cit:
        return COUNTRY.get(cit, "en")
    o = (guest.get("order_customer_language") or "").lower()
    return o if o in SUPPORTED else None


def tit(s):
    return " ".join(w.capitalize() if (w.isupper() or w.islower()) else w for w in (s or "").split())


def nome(guest):
    if not guest:
        return None
    # "Cognome N." : in Sala basta per riconoscere l'ospite e resta leggibile su due colonne
    def corto(cogn, nome_):
        cogn, nome_ = tit(cogn), tit(nome_)
        return (cogn + (" " + nome_[0] + "." if nome_ else "")).strip()
    return corto(guest.get("last_name"), guest.get("first_name")) or \
        corto(guest.get("order_customer_last_name"), guest.get("order_customer_first_name")) or None


def cifra(nomi, password, giorno):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(nomi, ensure_ascii=False).encode(), giorno.encode())
    return {"alg": "AES-GCM/PBKDF2-SHA256", "iter": ITER, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}


def main():
    stays = json.load(open(sys.argv[1], encoding="utf-8"))
    rows = json.load(open(sys.argv[2], encoding="utf-8"))["rows"]
    password, giorni = sys.argv[3], sys.argv[4:]
    per_res = collections.defaultdict(list)
    for r in rows:
        per_res[r["reservation_id"]].append(r)
    primario = {k: next((g for g in v if g.get("is_primary_guest")), v[0]) for k, v in per_res.items()}

    days, report = {}, []
    for d in giorni:
        rooms, nomi = {}, {}
        for s in stays:
            if not s.get("room") or not (s["arrival"] < d <= s["departure"]):
                continue
            assert s["room"] not in rooms, ("stanza doppia", d, s["room"])
            g = primario.get(s["reservation_id"])
            rooms[s["room"]] = {"max": int(s["people"]), "lang": lingua(g), "dep": s["departure"] == d}
            if nome(g):
                nomi[s["room"]] = nome(g)
        days[d] = {"rooms": dict(sorted(rooms.items(), key=lambda kv: int(kv[0]))), "names_enc": cifra(nomi, password, d)}
        report.append("%s: %d stanze, %d persone, %d partenze, %d fermate, %d nomi, lingue %s" % (
            d, len(rooms), sum(r["max"] for r in rooms.values()), sum(r["dep"] for r in rooms.values()),
            sum(not r["dep"] for r in rooms.values()), len(nomi),
            dict(collections.Counter(r["lang"] or "?" for r in rooms.values()).most_common())))
    out = {
        "property": "Alpstay – Smart Hotel Saslong", "source": "La Scatola",
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print("\n".join(report), file=sys.stderr)


if __name__ == "__main__":
    main()
