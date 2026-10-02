"""Riscrive il blocco ROSTER_EMBED dentro l'HTML con il contenuto di roster.json.
Uso: python3 incorpora_roster.py index.html roster.json"""
import json, re, sys
html_p, roster_p = sys.argv[1], sys.argv[2]
h = open(html_p, encoding='utf-8').read()
r = json.load(open(roster_p, encoding='utf-8'))
blob = json.dumps(r, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
new, n = re.subn(r'/\*ROSTER_EMBED_START\*/.*?/\*ROSTER_EMBED_END\*/',
                 lambda m: '/*ROSTER_EMBED_START*/const ROSTER_EMBEDDED = ' + blob + ';/*ROSTER_EMBED_END*/', h, flags=re.S)
assert n == 1, n
open(html_p, 'w', encoding='utf-8').write(new)
print('incorporati i giorni', list(r.get('days', {r.get('date'): 1}).keys()), 'in', html_p)
