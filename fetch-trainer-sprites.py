#!/usr/bin/env python3
"""
fetch-trainer-sprites.py v3
Source : Pokémon Showdown sprites (play.pokemonshowdown.com/sprites/trainers/)
Lance : python fetch-trainer-sprites.py
"""
import json, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

BASE = "https://play.pokemonshowdown.com/sprites/trainers"
MAP_FILE = Path(__file__).parent / "src" / "data" / "trainer-class-sprites.json"

# Mapping FR → slug Pokémon Showdown
# Slugs PS : lowercase, sans tiret sauf exceptions connues
CANDIDATES = {
    "Topdresseur":        ["acetrainer",     "ace-trainer"],
    "Topdresseuse":       ["acetrainerf",    "acetrainer-f"],
    "Topdresseurs":       ["acetrainer"],
    "Topdresseuse":       ["acetrainerf"],
    "Nageur":             ["swimmer",        "swimmerm"],
    "Nageurs":            ["swimmer"],
    "Nageuse":            ["swimmerf",       "swimmer-f"],
    "Pêcheur":            ["fisherman"],
    "Pêcheuse":           ["fisher",         "fisherman"],
    "Karatéka":           ["blackbelt"],
    "Gamin":              ["youngster"],
    "Montagnard":         ["hiker"],
    "Montagnarde":        ["hiker"],
    "Kinésiste":          ["tuber",          "tuberm"],
    "Fillette":           ["lass"],
    "Ornithologue":       ["birdkeeper"],
    "Champion":           ["champion",       "lance"],
    "Championne":         ["champion",       "iris"],
    "Champion d'Arène":   ["gymleader", "gym-leader", "leader", "gymleaderm", "misty", "brock"],
    "Championne d'Arène": ["gymleaderf", "gymleader-f", "leaderf", "misty", "jasmine"],
    "Ouvrier":            ["worker"],
    "Ouvrière":           ["worker"],
    "Vénérable":          ["sage"],
    "Scientifique":       ["scientist"],
    "Scout":              ["bugcatcher",     "bug-catcher"],
    "Marin":              ["sailor"],
    "Pokéfan":            ["pokefan",        "pokemaniac"],
    "Pique-Nique":        ["picnicker"],
    "Pique-nique":        ["picnicker"],
    "Canon":              ["juggler"],
    "Étudiant":           ["richboy",        "rich-boy"],
    "Étudiante":          ["lady"],
    "Combattante":        ["battlegirl",     "battle-girl"],
    "Campeur":            ["camper"],
    "Randonneur":         ["backpacker",     "hiker"],
    "Randonneuse":        ["backpackerf",    "backpacker-f"],
    "Dracologue":         ["dragontamer",    "dragon-tamer"],
    "Pokémaniac":         ["pokemaniac"],
    "Jumelles":           ["twins"],
    "Motard":             ["biker"],
    "Gentleman":          ["gentleman"],
    "Ruinemaniac":        ["ruinmaniac",     "ruin-maniac"],
    "Ruinophile":         ["ruinmaniac"],
    "Triathlète":         ["triathlete", "triathletebiker", "triathleteswimmer", "triathleterunner", "cyclist"],
    "Éleveur":            ["pokemonbreeder", "pokemon-breeder", "breeder"],
    "Éleveuse":           ["pokemonbreederf","breederf"],
    "Cycliste":           ["cyclist",        "biker"],
    "Écolier":            ["schoolkid",      "schoolboy"],
    "Écolière":           ["schoolkidf",     "schoolgirl"],
    "Guitariste":         ["guitarist"],
    "Ninja Fan":          ["ninjaboy",       "ninja-boy"],
    "Intello":            ["nerd", "supernerd", "super-nerd", "pokefan"],
    "Collectionneur":     ["collector"],
    "Flotteur":           ["tuber",          "tuberm"],
    "Petit":              ["youngster"],
    "Petite":             ["lass"],
    "Mademoiselle":       ["lady"],
    "Médium":             ["psychic",        "psychicm"],
    "Mystimaniac":        ["psychic"],
    "Pkmn Ranger":        ["pokemonranger",  "ranger"],
    "PKMN Ranger":        ["pokemonranger",  "ranger"],
    "Pokémon Ranger":     ["pokemonranger",  "ranger"],
    "Conseil":            ["elitefour", "elite-four", "agatha", "lorelei", "marshal"],
    "Conseil 4":          ["elitefour", "elite-four", "agatha", "lorelei", "marshal"],
    "Dresseur":           ["pokemontrainer", "red"],
    "Élève":              ["schoolkid"],
    "Loubard":            ["roughneck"],
    "Dompteur":           ["tamer", "cooltrainer", "acetrainer"],
    "Jongleur":           ["juggler"],
    "Mondaine":           ["beauty"],
    "Expert":             ["acetrainer"],
    "Experte":            ["acetrainerf"],
    "Motard":             ["biker"],
    "Randonneuse":        ["backpackerf"],
    "Marin":              ["sailor"],
    "Vaurienne":          ["lass"],
    "Vaurien":            ["youngster"],
    "Loubard":            ["roughneck"],
    "Danseur":            ["dancer"],
    "Danseuse":           ["dancer"],
}

sess = requests.Session()
results = {}
tested = {}

print(f"🔍 Test de {len(CANDIDATES)} classes sur Pokémon Showdown...\n")

for fr, slugs in CANDIDATES.items():
    found = None
    for slug in slugs:
        if slug in tested:
            if tested[slug]:
                found = slug
                break
            continue
        url = f"{BASE}/{slug}.png"
        try:
            r = sess.head(url, timeout=6)
            ok = r.status_code == 200
            tested[slug] = ok
            if ok:
                found = slug
                break
        except:
            tested[slug] = False
        time.sleep(0.05)

    if found:
        results[fr] = f"{BASE}/{found}.png"
        print(f"  ✅ {fr:30s} → {found}")
    else:
        print(f"  ❌ {fr:30s} (essayé: {', '.join(slugs)})")

print(f"\n{'='*55}")
print(f"✅ {len(results)}/{len(CANDIDATES)} classes avec sprite")

with open(MAP_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"📄 Sauvegardé → {MAP_FILE}")
