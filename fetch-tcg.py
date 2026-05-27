#!/usr/bin/env python3
"""
fetch-tcg.py — Récupère les cartes Pokémon TCG pour chaque Pokémon du site

Utilise l'API gratuite pokemontcg.io (sans clé, 1000 req/jour)
Recherche par numéro Pokédex national — fiable quelle que soit la langue.
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
ROOT = Path(__file__).parent
META = ROOT / "src" / "data" / "pokemon-meta.json"
DEST = ROOT / "src" / "data" / "pokemon-tcg.json"

API       = "https://api.pokemontcg.io/v2"
DELAY     = 1.1    # respecte la limite sans clé (~1000 req/jour)
CARDS_MAX = None     # cartes à conserver par Pokémon (None = illimité)
PAGE_SIZE = 250    # max autorisé par l'API

# ── Tri : on veut un mix de raretés, pas que des ultra-rares ─────
# Score de tri : on favorise la variété (holo classique > ultra rare > commun)
RARITY_RANK = {
    "Rare Holo":          10,   # icôniques, reconnaissables
    "Rare":                9,
    "Promo":               8,
    "Uncommon":            7,
    "Common":              6,   # les classiques Base Set etc.
    "Rare Holo V":         5,
    "Rare Holo VMAX":      5,
    "Rare Holo VSTAR":     5,
    "Rare Ultra":          4,
    "Rare Rainbow":        3,
    "Rare Secret":         3,
    "Rare Shiny":          3,
    "Rare Holo GX":        4,
    "Rare Holo EX":        4,
}

def rarity_score(card: dict) -> int:
    return RARITY_RANK.get(card.get("rarity", ""), 2)

def fetch_cards_for_dex(dex_id: int) -> list:
    """Récupère toutes les cartes d'un Pokémon par son numéro Pokédex."""
    all_cards = []
    page = 1
    while True:
        try:
            r = requests.get(
                f"{API}/cards",
                params={
                    "q":        f"nationalPokedexNumbers:{dex_id}",
                    "pageSize": PAGE_SIZE,
                    "page":     page,
                    "select":   "id,name,images,set,rarity,hp,artist,nationalPokedexNumbers",
                },
                timeout=30,
            )
            if r.status_code == 429:
                print("    ⏳ Rate limit — pause 60s...")
                time.sleep(60)
                continue
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}")

            data = r.json()
            batch = data.get("data", [])
            all_cards.extend(batch)

            # Pagination : si on a reçu PAGE_SIZE résultats il peut y en avoir plus
            if len(batch) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.5)  # pause entre pages
        except Exception as e:
            raise e
    return all_cards

# ── Charge les données existantes (reprise si relance) ───────────
existing: dict = {}
if DEST.exists():
    try:
        with open(DEST, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"📂 {len(existing)} Pokémon déjà traités — reprise\n")
    except Exception:
        print("⚠️  Fichier TCG existant illisible — repartir de zéro\n")

# ── Charge le meta Pokémon ────────────────────────────────────────
with open(META, encoding="utf-8") as f:
    meta = json.load(f)

total  = len(meta)
output = dict(existing)
ok     = 0
errors = []

print(f"🃏 Récupération des cartes TCG pour {total} Pokémon...\n")
print(f"   Recherche par numéro Pokédex — pageSize={PAGE_SIZE} — max={CARDS_MAX} cartes\n")

for i, (name_fr, data) in enumerate(meta.items(), 1):
    slug   = data.get("slug", "")
    dex_id = data.get("id", 0)

    if not slug or not dex_id:
        print(f"  [{i:3d}/{total}] ⚠️  {name_fr} — pas de slug/id")
        continue

    # Formes régionales (id > 10000) : utiliser l'id de l'espèce de base
    # car le numéro Pokédex national est celui de l'espèce de base
    real_dex = dex_id if dex_id <= 10000 else None
    if real_dex is None:
        # Tente de déduire depuis le slug (ex: "wooper-paldea" → cherche "wooper")
        print(f"  [{i:3d}/{total}] ⏭  {name_fr} — forme régionale, skip TCG")
        output.setdefault(slug, [])
        ok += 1
        continue

    # Saute si déjà traité (vérifie qu'on a bien cherché, même si 0 carte)
    if slug in output:
        ok += 1
        n = len(output[slug])
        print(f"  [{i:3d}/{total}] ⏭  {name_fr} ({n} carte{'s' if n != 1 else ''})")
        continue

    try:
        cards_raw = fetch_cards_for_dex(real_dex)

        # Filtre : doit avoir une image
        cards_with_img = [c for c in cards_raw if c.get("images", {}).get("small")]

        # Tri : mix rareté + date (pour avoir du Base Set ET des modernes)
        # Stratégie : trier par rareté d'abord, puis prendre CARDS_MAX
        cards_sorted = sorted(cards_with_img, key=rarity_score, reverse=True)

        limit = CARDS_MAX if CARDS_MAX else len(cards_sorted)
        cards = []
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
        total_found = len(cards_raw)
        print(f"  [{i:3d}/{total}] ✅ {name_fr:20s} → {len(cards)} cartes gardées / {total_found} trouvées (#{real_dex})")

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
print(f"🃏 {sum(len(v) for v in output.values())} cartes récupérées au total")
print(f"⚪ {no_cards} Pokémon sans carte TCG trouvée")
if errors:
    print(f"❌ {len(errors)} erreurs : {errors[:10]}")
print(f"📄 Sauvegardé → {DEST}")
print("\nRelance npm run build pour rebuilder le site.")
