#!/usr/bin/env python3
"""
build-data.py — Génère src/data/trainers.json enrichi depuis data/trainers.json
Lance depuis le dossier /site : python build-data.py
"""
import json, re, sys
from pathlib import Path
from collections import Counter

SRC  = Path(__file__).parent.parent / "data" / "trainers.json"
DEST = Path(__file__).parent / "src" / "data" / "trainers.json"
DEST.parent.mkdir(parents=True, exist_ok=True)

ACCENT_MAP = str.maketrans(
    "àâäéèêëîïôùûüçœæÀÂÄÉÈÊËÎÏÔÙÛÜÇŒÆ",
    "aaaeeeeiioouuucoaAAEEEEIIOUUUCOA"
)

def slugify(text: str) -> str:
    t = text.lower().translate(ACCENT_MAP)
    t = re.sub(r"[''`]", "-", t)
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")

def game_short(game: str) -> str:
    """Version courte du nom de jeu pour les slugs."""
    g = game.replace("Pokémon ", "").strip()
    return slugify(g)

with open(SRC, encoding="utf-8") as f:
    trainers = json.load(f)

# ── Comptage rareté par prénom ──────────────────────────────────
name_counts = Counter(t["name"] for t in trainers)

RARITY = [
    (0,  "unique",    "✨", "Introuvable",  "Aucun dresseur ne porte ce prénom !"),
    (1,  "legendaire","🏆", "Légendaire",   "Un seul dresseur légendaire porte ce prénom !"),
    (3,  "rare",      "💜", "Rare",         "Ce prénom est assez rare dans le monde Pokémon."),
    (10, "repandu",   "👀", "Répandu",      "Plusieurs dresseurs portent ce prénom."),
]

def get_rarity(count):
    if count == 0:   return RARITY[0]
    if count == 1:   return RARITY[1]
    if count <= 3:   return RARITY[2]
    if count <= 10:  return RARITY[3]
    return (count, "partout", "🔥", "Partout !", "Ce prénom est très populaire chez les dresseurs !")

# ── Enrichissement ──────────────────────────────────────────────
slug_seen = {}

for t in trainers:
    name_slug  = slugify(t["name"])
    class_slug = slugify(t.get("class", "dresseur"))
    game_slug  = game_short(t.get("game", ""))
    place_slug = slugify(t.get("place", ""))

    # Slug unique : classe-prenom-jeu (+ suffixe si collision)
    base_slug = f"{class_slug}-{name_slug}-{game_slug}"
    if base_slug in slug_seen:
        slug_seen[base_slug] += 1
        slug = f"{base_slug}-{slug_seen[base_slug]}"
    else:
        slug_seen[base_slug] = 0
        slug = base_slug

    cnt = name_counts[t["name"]]
    rar = get_rarity(cnt)

    t["slug"]          = slug
    t["name_slug"]     = name_slug
    t["class_slug"]    = class_slug
    t["game_slug"]     = game_slug
    t["place_slug"]    = place_slug
    t["rarity_key"]    = rar[1]
    t["rarity_emoji"]  = rar[2]
    t["rarity_label"]  = rar[3]
    t["rarity_desc"]   = rar[4]
    t["name_count"]    = cnt

with open(DEST, "w", encoding="utf-8") as f:
    json.dump(trainers, f, ensure_ascii=False, separators=(",", ":"))

print(f"✅ {len(trainers)} dresseurs → {DEST}")
print(f"   Slugs uniques : {len(slug_seen)}")
