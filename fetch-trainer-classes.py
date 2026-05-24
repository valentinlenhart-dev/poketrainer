#!/usr/bin/env python3
"""
fetch-trainer-classes.py — Traduit les classes de dresseurs via les CSV PokeAPI/Veekun

Génère src/data/trainer-classes-i18n.json :
  {
    "Gamin":       { "en": "Youngster", "de": "Knirps", "es": "Chico", "ja": "たんぱんこぞう", ... },
    "Topdresseur": { "en": "Ace Trainer", ... },
    ...
  }

Méthode : télécharge trainer_class_names.csv depuis le dépôt PokeAPI GitHub
(même technique que fetch-pokemon.py pour les noms d'espèces).

Lance : python fetch-trainer-classes.py
Durée : ~5 secondes (1 seul fichier CSV)
"""
import csv, io, json, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

SRC  = Path(__file__).parent / "src" / "data" / "trainers.json"
DEST = Path(__file__).parent / "src" / "data" / "trainer-classes-i18n.json"

# ── IDs de langue dans les CSV Veekun ────────────────────────────
LANG_MAP = {
    "5":  "fr",
    "9":  "en",
    "6":  "de",
    "7":  "es",
    "11": "ja",
    "8":  "it",
    "3":  "ko",
    "4":  "zh-Hans",
    "12": "zh-Hant",
    "13": "pt-BR",
}

# ── Récupère les classes uniques de la base ───────────────────────
with open(SRC, encoding="utf-8") as f:
    trainers = json.load(f)

fr_classes = sorted(set(t["class"] for t in trainers if t.get("class")))
print(f"🎯 {len(fr_classes)} classes distinctes dans trainers.json")

# ── Télécharge le CSV ─────────────────────────────────────────────
CSV_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/trainer_class_names.csv"
print(f"\n📥 Téléchargement de {CSV_URL}...")
try:
    r = requests.get(CSV_URL, timeout=20)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    print(f"✅ {len(rows)} lignes chargées")
except Exception as e:
    print(f"❌ Impossible de télécharger le CSV : {e}")
    sys.exit(1)

# ── Construit {trainer_class_id: {lang: name}} ───────────────────
by_id: dict[str, dict[str, str]] = {}
for row in rows:
    tid  = row.get("trainer_class_id", "").strip()
    lid  = row.get("local_language_id", "").strip()
    name = row.get("name", "").strip()
    lang = LANG_MAP.get(lid)
    if tid and lang and name:
        by_id.setdefault(tid, {})[lang] = name

print(f"   {len(by_id)} classes distinctes dans le CSV")

# ── Construit {fr_name: {lang: name}} ────────────────────────────
# Plusieurs IDs peuvent avoir le même nom FR (ex: même classe dans plusieurs régions)
# → on fusionne, la dernière valeur gagne (acceptable)
result: dict[str, dict[str, str]] = {}
matched = set()

for tid, names in by_id.items():
    fr_name = names.get("fr", "")
    if fr_name in fr_classes:
        if fr_name not in result:
            result[fr_name] = dict(names)
        else:
            # Fusionne : complète les langues manquantes
            for lang, val in names.items():
                if lang not in result[fr_name]:
                    result[fr_name][lang] = val
        matched.add(fr_name)

# ── Classes non matchées (classes locales, formes spéciales...) ──
unmatched = sorted(set(fr_classes) - matched)
print(f"\n✅ {len(matched)} classes matchées dans le CSV")
if unmatched:
    print(f"⚠️  {len(unmatched)} non matchées (classes custom / régionales) :")
    for c in unmatched[:20]:
        print(f"   - {c}")

# ── Sauvegarde ───────────────────────────────────────────────────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
import os
os.replace(_tmp, DEST)

print(f"\n📄 Sauvegardé → {DEST}  ({len(result)} entrées)")

# ── Résumé par langue ─────────────────────────────────────────────
print("\nCouverture par langue :")
all_langs = sorted({l for names in result.values() for l in names if l != "fr"})
for lang in all_langs:
    n = sum(1 for v in result.values() if lang in v)
    print(f"  {lang:10s} : {n}/{len(result)}")

print("\nRelance npm run build pour rebuilder le site.")
