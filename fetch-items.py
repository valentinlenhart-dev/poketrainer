#!/usr/bin/env python3
"""
fetch-items.py — Récupère les noms traduits de TOUS les objets équipables/tenus

Sources :
  1. Toutes les catégories d'objets "tenables" de la PokéAPI
  2. Tout objet avec held_by_pokemon non vide (filet de sécurité)

Génère src/data/items-i18n.json :
  { "oran-berry": { "fr": "Baie Oran", "en": "Oran Berry", "de": "...", "es": "...", "ja": "..." }, ... }

Lance : python fetch-items.py
Durée estimée : ~10-20 minutes selon le nombre d'objets (~300-500)
"""
import json, os, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

API   = "https://pokeapi.co/api/v2"
META  = Path(__file__).parent / "src" / "data" / "pokemon-meta.json"
DEST  = Path(__file__).parent / "src" / "data" / "items-i18n.json"
DELAY = 0.35

LANGS = ["fr", "en", "de", "es", "ja"]

# ── Catégories d'objets qui peuvent être tenus/équipés ────────────
HOLDABLE_CATEGORIES = {
    # Objets tenus généraux
    "held-items",
    "choice",               # Foulard/Lunettes/Bandeau Choix
    "bad-held-items",       # Bulle Collante, Anneau Cible...
    "type-enhancement",     # Charbon, Eau Mystique, Poings Noirs...
    "other",                # Restes, Casque Hérisson, Cuillère Tordue...
    "species-specific",     # Orbe Éclat, Bâton Épais, Âme Rosée...
    "loot",                 # Objet Chance, Écaille Cœur...
    "collectibles",         # Œuf Chance, Étoile Écarlate...
    # Pierres et évolutions tenables
    "plates",               # Plaques d'Arceus
    "memories",             # Disques de Silvallié
    "jewels",               # Joyaux élémentaires
    "mega-stones",          # Méga-Gemmes
    "z-crystals",           # Cristaux Z
    # Baies (toutes tenables)
    "berries",
    "in-a-pinch-berries",   # Baies Sitrus, Pêche...
    "picky-healing-berries",
    "type-protection-berries",
    "effort-drop",          # Baies réducteurs de stats
    "baked-goods",          # Monsieur Mime Ice Cream...
    # Mail (tenu pour transférer messages)
    "all-mail",
    # Autres équipables
    "miracle-shooter",      # Objets Miraculous (B2W2)
    "stat-boosts",          # certains sont tenus (Poudre X mais pas en combat... skip si vide)
    "scarves",              # Foulards concours (Concours Pokémon)
    "contest-mixes",        # Ingrédients de concours
    "flutes",               # Flûtes (certaines versions)
}

# ── Charge l'existant ─────────────────────────────────────────────
existing: dict = {}
if DEST.exists():
    try:
        existing = json.load(open(DEST, encoding="utf-8"))
        print(f"📂 {len(existing)} objets déjà traités — reprise\n")
    except Exception:
        pass

# ── Collecter les slugs depuis held_items du meta (filet de sécurité) ──
meta_held: set[str] = set()
if META.exists():
    try:
        meta = json.load(open(META, encoding="utf-8"))
        for d in meta.values():
            for h in d.get("held_items", []):
                meta_held.add(h["item"])
        print(f"🎒 {len(meta_held)} objets tenus dans pokemon-meta.json\n")
    except Exception:
        pass

# ── Récupère tous les items des catégories holdables ──────────────
def fetch_category_items(category: str) -> list[str]:
    """Retourne la liste des slugs d'items d'une catégorie."""
    try:
        r = requests.get(f"{API}/item-category/{category}", timeout=10)
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            print(f"    ⚠️  Catégorie {category}: HTTP {r.status_code}")
            return []
        return [i["name"] for i in r.json().get("items", [])]
    except Exception as e:
        print(f"    ⚠️  Catégorie {category}: {e}")
        return []

print("📦 Récupération des listes par catégorie...")
to_fetch: set[str] = set(meta_held)  # commence avec les objets du meta

for cat in sorted(HOLDABLE_CATEGORIES):
    items_in_cat = fetch_category_items(cat)
    if items_in_cat:
        print(f"  ✓ {cat}: {len(items_in_cat)} objets")
        to_fetch.update(items_in_cat)
    time.sleep(0.2)

print(f"\n🎯 Total unique à traduire : {len(to_fetch)} objets")
print(f"   (dont {len(existing)} déjà traités)\n")

# ── Traduit chaque objet ──────────────────────────────────────────
def fetch_item_i18n(slug: str) -> dict[str, str] | None:
    """Retourne {fr, en, de, es, ja} pour un objet, ou None si échec."""
    try:
        r = requests.get(f"{API}/item/{slug}", timeout=10)
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        d = r.json()
        names: dict[str, str] = {}
        for n in d.get("names", []):
            lang = n["language"]["name"]
            if lang in LANGS:
                names[lang] = n["name"]
        fallback = slug.replace("-", " ").title()
        return {lang: names.get(lang, fallback) for lang in LANGS}
    except Exception as e:
        raise e

output = dict(existing)
ok, skipped, errors = 0, 0, []
total = len(to_fetch)

for i, slug in enumerate(sorted(to_fetch), 1):
    if slug in output:
        skipped += 1
        continue

    try:
        result = fetch_item_i18n(slug)
        if result is None:
            print(f"  [{i:3d}/{total}] ⚠️  {slug} — introuvable (404)")
            skipped += 1
            continue

        output[slug] = result
        ok += 1
        fr_name = result.get("fr", "?")
        en_name = result.get("en", "?")
        print(f"  [{i:3d}/{total}] ✅ {slug:35s} {fr_name} / {en_name}")

    except Exception as e:
        errors.append(slug)
        print(f"  [{i:3d}/{total}] ❌ {slug}: {e}")

    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 50 entrées
    if ok > 0 and ok % 50 == 0:
        _tmp = DEST.with_suffix(".tmp")
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        os.replace(_tmp, DEST)
        print(f"\n  💾 Sauvegarde intermédiaire ({ok} nouveaux)\n")

# ── Sauvegarde finale atomique (évite la corruption du JSON) ──────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
os.replace(_tmp, DEST)

print(f"\n{'='*55}")
print(f"✅ {ok} nouveaux objets traduits")
print(f"⏭  {skipped} déjà présents / introuvables")
if errors:
    print(f"❌ {len(errors)} erreurs : {errors[:10]}")
print(f"📄 Total dans le fichier : {len(output)} objets")
print(f"📄 Sauvegardé → {DEST}")
print("\nRelance npm run build pour rebuilder le site.")
