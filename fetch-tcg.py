#!/usr/bin/env python3
"""
fetch-tcg.py — Récupère les cartes Pokémon TCG pour chaque Pokémon du site

Utilise l'API gratuite pokemontcg.io (sans clé, 1000 req/jour)
Génère src/data/pokemon-tcg.json :
  { "pikachu": [ {id, name, image, set, rarity, hp, artist}, ... ] }

Lance : python fetch-tcg.py
Durée estimée : ~15 minutes (886 Pokémon × 1s de délai)
"""
import json, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

# ── Chemins ──────────────────────────────────────────────────────
ROOT      = Path(__file__).parent
META      = ROOT / "src" / "data" / "pokemon-meta.json"
DEST      = ROOT / "src" / "data" / "pokemon-tcg.json"

API       = "https://api.pokemontcg.io/v2"
DELAY     = 1.1   # respecte la limite sans clé (1000/jour ≈ 1 req/s max)
CARDS_MAX = 20    # cartes à conserver par Pokémon (None = illimité)

# Raretés qu'on préfère afficher (dans l'ordre de préférence)
RARITY_RANK = {
    "Rare Holo VMAX": 10,
    "Rare Holo VSTAR": 10,
    "Rare Holo V": 9,
    "Rare Ultra": 9,
    "Rare Rainbow": 8,
    "Rare Secret": 8,
    "Rare Shiny": 7,
    "Rare Holo": 7,
    "Rare": 6,
    "Uncommon": 4,
    "Common": 3,
    "Promo": 5,
}

def rarity_score(card: dict) -> int:
    return RARITY_RANK.get(card.get("rarity", ""), 2)

# ── Charge les données existantes (si relance) ───────────────────
existing: dict = {}
if DEST.exists():
    with open(DEST, encoding="utf-8") as f:
        existing = json.load(f)

# ── Charge les Pokémon ────────────────────────────────────────────
with open(META, encoding="utf-8") as f:
    meta = json.load(f)

total  = len(meta)
output = dict(existing)  # copie pour reprise
ok     = 0
errors = []

print(f"🃏 Récupération des cartes TCG pour {total} Pokémon...\n")
print(f"   (API gratuite — délai {DELAY}s entre requêtes)\n")

for i, (name_fr, data) in enumerate(meta.items(), 1):
    slug = data.get("slug", "")
    if not slug:
        continue

    # Saute si déjà récupéré
    if slug in output:
        ok += 1
        print(f"  [{i:3d}/{total}] ⏭  {name_fr} (déjà récupéré, {len(output[slug])} cartes)")
        continue

    # L'API TCG utilise les noms anglais
    # On cherche par slug converti en nom propre
    en_name = slug.replace("-", " ").title()

    try:
        r = requests.get(
            f"{API}/cards",
            params={
                "q":        f'name:"{en_name}"',
                "pageSize": 20,
                "orderBy":  "-set.releaseDate",
                "select":   "id,name,images,set,rarity,hp,artist",
            },
            timeout=15,
        )
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")

        cards_raw = r.json().get("data", [])

        # Filtre les cartes avec image + trie par rareté
        cards_with_img = [c for c in cards_raw if c.get("images", {}).get("small")]
        cards_sorted   = sorted(cards_with_img, key=rarity_score, reverse=True)

        cards = []
        limit = CARDS_MAX if CARDS_MAX else len(cards_sorted)
        for c in cards_sorted[:limit]:
            cards.append({
                "id":     c["id"],
                "name":   c["name"],
                "image":  c["images"]["small"],
                "set":    c.get("set", {}).get("name", ""),
                "rarity": c.get("rarity", ""),
                "hp":     c.get("hp", ""),
                "artist": c.get("artist", ""),
            })

        output[slug] = cards
        ok += 1
        card_info = f"{len(cards)} carte(s)" if cards else "aucune carte"
        print(f"  [{i:3d}/{total}] ✅ {name_fr:20s} → {card_info}")

    except Exception as e:
        errors.append(name_fr)
        print(f"  [{i:3d}/{total}] ❌ {name_fr}: {e}")

    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 50 entrées
    if i % 50 == 0:
        with open(DEST, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
        print(f"\n  💾 Sauvegarde intermédiaire ({i}/{total})\n")

# ── Sauvegarde finale ─────────────────────────────────────────────
with open(DEST, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

no_cards = sum(1 for v in output.values() if not v)
print(f"\n{'='*55}")
print(f"✅ {ok}/{total} Pokémon traités")
print(f"🃏 {sum(len(v) for v in output.values())} cartes récupérées")
print(f"⚪ {no_cards} Pokémon sans carte TCG trouvée")
if errors:
    print(f"❌ {len(errors)} erreurs : {errors[:10]}")
print(f"📄 Sauvegardé → {DEST}")
print("\nRelance npm run build pour rebuilder le site.")
