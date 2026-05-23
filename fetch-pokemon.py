#!/usr/bin/env python3
"""
fetch-pokemon.py v3 — Index officiel PokéAPI + noms français.

Étape 1 : Télécharge le CSV officiel des noms FR depuis GitHub PokeAPI
          (1 seul fichier, ~200 Ko, couvre les 1025 espèces)
Étape 2 : Enrichit chaque Pokémon unique de la base

Lance : python fetch-pokemon.py
"""
import csv, io, json, os, re, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

SRC   = Path(__file__).parent / "src" / "data" / "trainers.json"
DEST  = Path(__file__).parent / "src" / "data" / "pokemon-meta.json"
API   = "https://pokeapi.co/api/v2"
DELAY = 0.25

# ── 0. Nettoyage des noms corrompus ─────────────────────────────
def clean_name(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r'\s*[Nn]iveau\s*\d+.*$', '', s)
    s = re.sub(r'\s*\(.*?\)\s*$', '', s)
    return s.strip()

with open(SRC, encoding="utf-8") as f:
    trainers = json.load(f)

all_pokemon = {clean_name(p) for t in trainers for p in t.get("team", [])}
all_pokemon.discard("")
print(f"🎯 {len(all_pokemon)} Pokémon distincts à enrichir")

# ── 1. Index FR→ID depuis le CSV officiel PokéAPI ───────────────
CSV_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_species_names.csv"
# Colonnes : pokemon_species_id, local_language_id, name, genus
# local_language_id = 5 → Français

print("\n📥 Téléchargement de l'index des noms officiels PokéAPI...")
try:
    r = requests.get(CSV_URL, timeout=20)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))

    fr_to_id = {}   # nom_fr → species_id
    for row in reader:
        if row.get("local_language_id") == "5":  # FR
            name_fr = row["name"].strip()
            sid     = int(row["pokemon_species_id"])
            fr_to_id[name_fr.lower()] = sid

    print(f"✅ {len(fr_to_id)} noms français indexés")
except Exception as e:
    print(f"❌ Impossible de charger le CSV : {e}")
    print("   → Le script va tenter la normalisation directe comme fallback.")
    fr_to_id = {}

# ── Normalisation fallback ───────────────────────────────────────
def normalize_slug(name: str) -> str:
    n = name.lower()
    for a, b in [('é','e'),('è','e'),('ê','e'),('à','a'),('ç','c'),
                 ('ô','o'),('û','u'),('î','i'),('â','a'),('ï','i'),
                 ('œ','oe'),('♀','-f'),('♂','-m'),("'","-"),("'","-")]:
        n = n.replace(a, b)
    n = re.sub(r'[^a-z0-9\-]', '', n)
    return n.strip('-')

# ── 2. Charge les données existantes (merge-safe) ────────────────
# On préserve les champs ajoutés par fetch-pokemon-species.py
SPECIES_FIELDS = {
    "description_fr", "descriptions_fr", "category_fr", "generation",
    "capture_rate", "is_legendary", "is_mythical", "gender_fr",
    "habitat_fr", "base_happiness", "hatch_counter",
    "evolves_from", "evolves_to", "abilities",
}

existing = {}
if DEST.exists():
    try:
        with open(DEST, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"📂 {len(existing)} entrées existantes chargées (les données species seront préservées)\n")
    except Exception as e:
        print(f"⚠️  Impossible de charger l'existant ({e}) — repartir de zéro\n")

# ── 3. Enrichissement ────────────────────────────────────────────
# On part de l'existant : seules les entrées MANQUANTES ou avec id=0 sont re-fetchées
results = dict(existing)
errors  = []
ok      = 0
skipped = 0
to_fetch = [n for n in sorted(all_pokemon) if n not in results or results[n].get("id", 0) == 0]
total   = len(to_fetch)

print(f"\n🔍 {len(all_pokemon)} Pokémon distincts ({len(results)} déjà en cache, {total} à fetcher)...\n")

for i, name in enumerate(to_fetch, 1):
    # Chercher l'ID via l'index FR
    species_id = fr_to_id.get(name.lower())

    if species_id:
        # Requête directe par ID (très fiable)
        url = f"{API}/pokemon/{species_id}"
    else:
        # Fallback : normalisation du nom FR
        url = f"{API}/pokemon/{normalize_slug(name)}"

    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            d = r.json()
            pid = d["id"]
            sp  = d.get("sprites", {})
            sp_other = sp.get("other", {})

            # Récupère les données species existantes pour ce Pokémon
            prev = existing.get(name, {})
            species_data = {k: v for k, v in prev.items() if k in SPECIES_FIELDS}

            results[name] = {
                **species_data,   # préserve description_fr, abilities, etc.

                # ── Identité ──────────────────────────────────────
                "id":     pid,
                "slug":   d["name"],

                # ── Sprites pixel art ─────────────────────────────
                "sprite":        sp.get("front_default"),
                "sprite_shiny":  sp.get("front_shiny"),
                "sprite_female": sp.get("front_female"),  # ♀ si différent

                # ── Artwork HD officiel ───────────────────────────
                "sprite_hd":       sp_other.get("official-artwork", {}).get("front_default")
                                   or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pid}.png",
                "sprite_hd_shiny": sp_other.get("official-artwork", {}).get("front_shiny"),

                # ── Sprite animé Showdown ─────────────────────────
                "sprite_anim":       sp_other.get("showdown", {}).get("front_default"),
                "sprite_anim_shiny": sp_other.get("showdown", {}).get("front_shiny"),

                # ── Types ─────────────────────────────────────────
                "types":      [t["type"]["name"] for t in d.get("types", [])],
                "past_types": [
                    {
                        "gen":   pt["generation"]["name"],
                        "types": [t["type"]["name"] for t in pt["types"]],
                    }
                    for pt in d.get("past_types", [])
                ],

                # ── Stats de base ─────────────────────────────────
                "stats":           {s["stat"]["name"]: s["base_stat"] for s in d.get("stats", [])},
                "base_experience": d.get("base_experience"),

                # ── Morphologie ───────────────────────────────────
                "height": d["height"],   # en décimètres
                "weight": d["weight"],   # en hectogrammes

                # ── Objets tenus dans la nature ───────────────────
                "held_items": [
                    {
                        "item":  hi["item"]["name"],
                        "rarity": hi["version_details"][-1]["rarity"] if hi.get("version_details") else None,
                    }
                    for hi in d.get("held_items", [])
                ],

                # ── Jeux où le Pokémon apparaît ───────────────────
                "game_indices": [gi["version"]["name"] for gi in d.get("game_indices", [])],
            }
            ok += 1
            status = f"✅ {name} → #{pid} ({d['name']})"
        else:
            raise ValueError(f"HTTP {r.status_code}")
    except Exception as e:
        errors.append(name)
        results[name] = {"id": 0, "slug": normalize_slug(name), "sprite": None, "sprite_hd": None, "types": [], "stats": {}}
        status = f"⚠️  {name} → {e}"

    print(f"  [{i:3d}/{total}] {status}")
    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 100 entrées
    if i % 100 == 0:
        _tmp = DEST.with_suffix(".tmp")
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(_tmp, DEST)
        print(f"\n  💾 Sauvegarde intermédiaire ({i}/{total})\n")

# ── Sauvegarde finale atomique ────────────────────────────────────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(_tmp, DEST)

print(f"\n{'='*55}")
print(f"✅ {ok}/{total} Pokémon enrichis avec sprites et stats")
if errors:
    print(f"⚠️  {len(errors)} introuvables (formes spéciales ou données corrompues) :")
    for e in errors[:15]:
        print(f"   - {e}")
print(f"📄 Sauvegardé → {DEST}")
