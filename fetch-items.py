#!/usr/bin/env python3
"""
fetch-items.py — Récupère les données complètes de tous les objets équipables

Génère src/data/items-meta.json :
  {
    "leftovers": {
      "slug": "leftovers",
      "names":   { "fr": "Restes", "en": "Leftovers", ... },
      "sprite":  "https://...sprites/items/leftovers.png",
      "cost":    100,
      "category": "held-items",
      "attributes": ["holdable", "holdable-passive"],
      "effect_en":       "Restores 1/16 max HP each turn.",
      "effect_long_en":  "...",
      "flavors": { "fr": { "Épée": "..." }, "en": {...}, "de": {...}, "es": {...}, "ja": {...} },
      "held_by": [ { "slug": "snorlax", "rarity": 50 }, ... ],
      "generations": ["ii", "iii", "iv"],
      "fling_power": 10,
      "fling_effect_en": null
    }
  }

Génère aussi src/data/items-i18n.json (rétrocompat) :
  { "leftovers": { "fr": "Restes", "en": "Leftovers", ... } }

Lance : python fetch-items.py
Durée estimée : ~15-25 minutes (~400-600 objets × 1 appel)
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
DEST  = Path(__file__).parent / "src" / "data" / "items-meta.json"
DEST_I18N = Path(__file__).parent / "src" / "data" / "items-i18n.json"
DELAY = 0.35

LANGS = ["fr", "en", "de", "es", "ja", "it", "ko", "zh-Hans"]

# ── Labels de version_group → label FR ───────────────────────────
VG_FR = {
    "gold-silver": "Or et Argent",
    "crystal": "Cristal",
    "ruby-sapphire": "Rubis Saphir",
    "emerald": "Émeraude",
    "firered-leafgreen": "Rouge Feu Vert Feuille",
    "diamond-pearl": "Diamant Perle",
    "platinum": "Platine",
    "heartgold-soulsilver": "HeartGold SoulSilver",
    "black-white": "Noir et Blanc",
    "black-2-white-2": "Noir 2 et Blanc 2",
    "x-y": "X et Y",
    "omega-ruby-alpha-sapphire": "Rubis Oméga Saphir Alpha",
    "sun-moon": "Soleil et Lune",
    "ultra-sun-ultra-moon": "Ultra-Soleil et Ultra-Lune",
    "lets-go-pikachu-lets-go-eevee": "Pikachu et Évoli",
    "sword-shield": "Épée et Bouclier",
    "brilliant-diamond-and-shining-pearl": "Diamant Étincelant Perle Scintillante",
    "legends-arceus": "Légendes : Arceus",
    "scarlet-violet": "Écarlate et Violet",
    "red-blue": "Rouge et Bleu",
    "yellow": "Jaune",
    "colosseum": "Colosseum",
    "xd": "XD : Le Souffle des Ténèbres",
}

# ── Catégories d'objets qui peuvent être tenus/équipés ────────────
HOLDABLE_CATEGORIES = {
    "held-items", "choice", "bad-held-items", "type-enhancement",
    "other", "species-specific", "loot", "collectibles",
    "plates", "memories", "jewels", "mega-stones", "z-crystals",
    "berries", "in-a-pinch-berries", "picky-healing-berries",
    "type-protection-berries", "effort-drop", "baked-goods",
    "all-mail", "miracle-shooter", "stat-boosts", "scarves",
    "contest-mixes", "flutes",
}

# ── Charge l'existant ─────────────────────────────────────────────
existing: dict = {}
if DEST.exists():
    try:
        existing = json.load(open(DEST, encoding="utf-8"))
        print(f"📂 {len(existing)} objets déjà traités — reprise\n")
    except Exception as e:
        print(f"⚠️  items-meta.json illisible ({e}) — reprise depuis zéro\n")

# ── Récupère les slugs depuis pokemon-meta (filet de sécurité) ────
meta_held: set[str] = set()
if META.exists():
    try:
        pkmeta = json.load(open(META, encoding="utf-8"))
        for d in pkmeta.values():
            for h in d.get("held_items", []):
                meta_held.add(h["item"])
        print(f"🎒 {len(meta_held)} objets tenus dans pokemon-meta.json\n")
    except Exception as e:
        print(f"⚠️  pokemon-meta.json illisible : {e}\n")

# ── Récupère les slugs par catégorie ──────────────────────────────
def fetch_category_items(category: str) -> list[str]:
    try:
        r = requests.get(f"{API}/item-category/{category}", timeout=10)
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            return []
        return [i["name"] for i in r.json().get("items", [])]
    except Exception:
        return []

print("📦 Récupération des listes par catégorie...")
to_fetch: set[str] = set(meta_held)
for cat in sorted(HOLDABLE_CATEGORIES):
    items_in_cat = fetch_category_items(cat)
    if items_in_cat:
        print(f"  ✓ {cat}: {len(items_in_cat)} objets")
        to_fetch.update(items_in_cat)
    time.sleep(0.2)

print(f"\n🎯 Total unique à enrichir : {len(to_fetch)} objets")
print(f"   (dont {len(existing)} déjà traités)\n")

# ── Fetch et enrichissement ───────────────────────────────────────
output = dict(existing)
ok, skipped, errors = 0, 0, []
total = len(to_fetch)

for i, slug in enumerate(sorted(to_fetch), 1):
    # Re-fetch si les nouvelles langues (it/ko/zh-Hans) manquent dans l'entrée existante
    if slug in output:
        existing_names = output[slug].get("names", {})
        if "it" in existing_names and "ko" in existing_names and "zh-Hans" in existing_names:
            skipped += 1
            continue

    try:
        r = requests.get(f"{API}/item/{slug}", timeout=10)
        if r.status_code == 404:
            skipped += 1
            continue
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        d = r.json()

        # ── Noms traduits (5 langues) ─────────────────────────────
        names: dict[str, str] = {}
        fallback = slug.replace("-", " ").title()
        for n in d.get("names", []):
            lang = n["language"]["name"]
            if lang in LANGS:
                names[lang] = n["name"]
        names_out = {lang: names.get(lang, fallback) for lang in LANGS}

        # ── Sprite ────────────────────────────────────────────────
        sprites = d.get("sprites", {})
        sprite = sprites.get("default") or None

        # ── Prix ──────────────────────────────────────────────────
        cost = d.get("cost", 0)

        # ── Catégorie et attributs ────────────────────────────────
        category = d.get("category", {}).get("name", "")
        attributes = [a["name"] for a in d.get("attributes", [])]

        # ── Effet (surtout disponible en EN) ──────────────────────
        effect_en = ""
        effect_long_en = ""
        for e in d.get("effect_entries", []):
            if e["language"]["name"] == "en":
                effect_en      = e.get("short_effect", "").replace("\n", " ").strip()
                effect_long_en = e.get("effect", "").replace("\n", " ").strip()
                break

        # ── Descriptions par version_group + langue ───────────────
        flavors: dict[str, dict[str, str]] = {lang: {} for lang in LANGS}
        for ft in d.get("flavor_text_entries", []):
            lang = ft["language"]["name"]
            if lang not in LANGS:
                continue
            vg = ft.get("version_group", {}).get("name", "")
            label = VG_FR.get(vg, vg.replace("-", " ").title())
            text = ft["text"].replace("\n", " ").replace("\f", " ").strip()
            # Ne garde que la dernière entrée par label (déduplique)
            flavors[lang][label] = text

        # ── Pokémon qui tiennent cet objet ────────────────────────
        held_by = []
        for h in d.get("held_by_pokemon", []):
            pk_slug = h["pokemon"]["name"]
            details = h.get("version_details", [])
            max_rarity = max((v["rarity"] for v in details), default=0) if details else 0
            held_by.append({"slug": pk_slug, "rarity": max_rarity})
        # Tri : porteurs les plus fréquents d'abord
        held_by.sort(key=lambda x: -x["rarity"])

        # ── Générations disponibles ───────────────────────────────
        generations = sorted(set(
            g["generation"]["name"].replace("generation-", "")
            for g in d.get("game_indices", [])
        ))

        # ── Fling ─────────────────────────────────────────────────
        fling_power      = d.get("fling_power")
        fling_effect_raw = d.get("fling_effect")
        fling_effect_en  = fling_effect_raw["name"] if fling_effect_raw else None

        # ── Stockage ──────────────────────────────────────────────
        output[slug] = {
            "slug":           slug,
            "names":          names_out,
            "sprite":         sprite,
            "cost":           cost,
            "category":       category,
            "attributes":     attributes,
            "effect_en":      effect_en,
            "effect_long_en": effect_long_en,
            "flavors":        flavors,
            "held_by":        held_by,
            "generations":    generations,
            "fling_power":    fling_power,
            "fling_effect_en": fling_effect_en,
        }

        ok += 1
        fr_name = names_out.get("fr", slug)
        print(f"  [{i:3d}/{total}] ✅ {slug:40s} {fr_name}")

    except Exception as e:
        errors.append(slug)
        print(f"  [{i:3d}/{total}] ❌ {slug}: {e}")

    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 50 nouvelles entrées
    if ok > 0 and ok % 50 == 0:
        _tmp = DEST.with_suffix(".tmp")
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(_tmp, DEST)
        print(f"\n  💾 Sauvegarde intermédiaire items-meta.json ({ok} nouveaux)\n")

# ── Sauvegarde finale items-meta.json ─────────────────────────────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(_tmp, DEST)

# ── Génère items-i18n.json (rétrocompatibilité) ───────────────────
i18n = {slug: data["names"] for slug, data in output.items()}
_tmp2 = DEST_I18N.with_suffix(".tmp")
with open(_tmp2, "w", encoding="utf-8") as f:
    json.dump(i18n, f, ensure_ascii=False, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(_tmp2, DEST_I18N)

print(f"\n{'='*55}")
print(f"✅ {ok} nouveaux objets enrichis")
print(f"⏭  {skipped} déjà présents / introuvables")
if errors:
    print(f"❌ {len(errors)} erreurs : {errors[:10]}")
print(f"📄 items-meta.json : {len(output)} objets")
print(f"📄 items-i18n.json : {len(i18n)} objets (rétrocompat)")
print("\nRelance npm run build pour rebuilder le site.")
