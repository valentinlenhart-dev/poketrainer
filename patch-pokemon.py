#!/usr/bin/env python3
"""
patch-pokemon.py — Corrige les 63 entrées manquantes dans pokemon-meta.json.
Lance depuis site/ : python patch-pokemon.py
"""
import json
from pathlib import Path

DEST = Path(__file__).parent / "src" / "data" / "pokemon-meta.json"
meta = json.loads(DEST.read_text(encoding="utf-8"))

# Formes Gigamax / Dynamax / spéciales → copie depuis la forme de base
# Typos → copie depuis le nom correct
ALIASES = {
    "Azumaril":   "Azumarill",
    "Carvahna":   "Carvanha",
    "Cadoiozo":   "Cadoizo",
    "Barguantua": "Bargantua",
    # Gigamax → forme de base
    "G-Charmilly":  "Charmilly",
    "G-Duralugon":  "Duralugon",
    "G-Ectoplasma": "Ectoplasma",
    # Formes spéciales → forme de base
    "Axoloto-P":  "Axoloto",
    "D-Blancoton":"Blancoton",
    "D-Ronflex":  "Ronflex",
    "D-Torgamord":"Torgamord",
    "Fragroin-F": "Fragroin",
}

patched = 0
for alias, target in ALIASES.items():
    is_missing = alias not in meta or meta[alias].get("id", 0) == 0
    target_ok  = target in meta and meta[target].get("id", 0) != 0
    if is_missing and target_ok:
        meta[alias] = dict(meta[target])
        patched += 1
        print(f"  ✅ {alias} → copié depuis {target} (#{meta[target]['id']})")
    else:
        print(f"  ⏭  {alias} → déjà ok ou target introuvable")

DEST.write_text(
    json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8"
)
print(f"\n✅ {patched} entrées corrigées sur {len(ALIASES)} tentées")
print(f"📄 {DEST}")
