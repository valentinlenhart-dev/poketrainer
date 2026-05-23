#!/usr/bin/env python3
"""
fix-missing-categories.py — Complète uniquement category_en/de/es/ja manquants

Beaucoup plus rapide que fetch-pokemon-species.py car :
  - 1 seul appel API par Pokémon (species endpoint)
  - Ne touche pas aux descriptions, talents, évolutions déjà présents
  - Traite uniquement les 218 entrées sans category_en

Lance : python fix-missing-categories.py
Durée estimée : ~3-4 minutes
"""
import json, os, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

API  = "https://pokeapi.co/api/v2"
DEST = Path(__file__).parent / "src" / "data" / "pokemon-meta.json"
DELAY = 0.25
LANGS = ["fr", "en", "de", "es", "ja"]

# ── Charge l'existant ─────────────────────────────────────────────
with open(DEST, encoding="utf-8") as f:
    meta = json.load(f)

# ── Identifie les cibles ──────────────────────────────────────────
targets = {
    name: data for name, data in meta.items()
    if data.get("category_fr") and not data.get("category_en") and data.get("id")
}
print(f"🎯 {len(targets)} Pokémon avec category_fr mais sans category_en\n")

ok, errors = 0, []

for i, (name_fr, data) in enumerate(targets.items(), 1):
    species_id = data["id"]
    try:
        r = requests.get(f"{API}/pokemon-species/{species_id}", timeout=10)
        if r.status_code != 200:
            # Fallback via /pokemon/
            pr = requests.get(f"{API}/pokemon/{species_id}", timeout=10)
            if pr.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")
            species_url = pr.json().get("species", {}).get("url", "")
            r = requests.get(species_url, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code} (fallback)")
            time.sleep(0.2)

        s = r.json()
        categories = {}
        for g in s.get("genera", []):
            lang = g["language"]["name"]
            if lang in LANGS:
                categories[lang] = g["genus"]

        if not categories.get("en"):
            # PokéAPI ne renvoie pas de catégorie EN pour ce Pokémon
            print(f"  [{i:3d}/{len(targets)}] ⚠️  {name_fr}: pas de category_en dans l'API")
            errors.append(name_fr)
            continue

        cat_fr = data.get("category_fr", "")
        data["category_en"] = categories.get("en", cat_fr)
        data["category_de"] = categories.get("de", cat_fr)
        data["category_es"] = categories.get("es", cat_fr)
        data["category_ja"] = categories.get("ja", cat_fr)

        ok += 1
        print(f"  [{i:3d}/{len(targets)}] ✅ {name_fr:20s} → {data['category_en']}")

    except Exception as e:
        errors.append(name_fr)
        print(f"  [{i:3d}/{len(targets)}] ❌ {name_fr}: {e}")

    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 50 entrées
    if ok > 0 and ok % 50 == 0:
        _tmp = DEST.with_suffix(".tmp")
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(_tmp, DEST)
        print(f"\n  💾 Sauvegarde intermédiaire ({ok}/{len(targets)})\n")

# ── Sauvegarde finale ──────────────────────────────────────────────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(_tmp, DEST)

print(f"\n{'='*55}")
print(f"✅ {ok}/{len(targets)} categories complétées")
if errors:
    print(f"⚠️  {len(errors)} erreurs/absences API : {errors[:10]}")
print(f"📄 Sauvegardé → {DEST}")
print("\nRelance npm run build pour rebuilder le site.")
