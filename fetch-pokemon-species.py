#!/usr/bin/env python3
"""
fetch-pokemon-species.py — Enrichit pokemon-meta.json avec les données d'espèce PokeAPI

Données ajoutées :
  description_fr      — dernière description Pokédex en français
  descriptions_fr/en/de/es/ja  — dict {jeu_fr: description} par langue
  category_fr         — "Pokémon Souris", "Pokémon Feu"...
  generation          — "Génération I"...
  capture_rate        — 0-255
  is_legendary        — booléen
  is_mythical         — booléen
  gender_fr           — % femelle ou "Asexué"
  habitat_fr          — "Grotte", "Forêt", "Mer"... (null si inconnu)
  base_happiness      — bonheur de base (0-255)
  hatch_counter       — cycles d'éclosion (~255 pas chacun)
  evolves_from        — slug anglais du pré-évolution (null si aucun)
  evolves_to          — liste de slugs anglais des évolutions directes
  abilities           — liste de {name_fr/en/de/es/ja, desc_fr/en/de/es/ja, is_hidden}

Lance : python fetch-pokemon-species.py
Durée estimée : ~18 minutes (886 Pokémon × 2 appels + cache talents)
"""
import json, os, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

API   = "https://pokeapi.co/api/v2"
DEST  = Path(__file__).parent / "src" / "data" / "pokemon-meta.json"
DELAY = 0.3

# ── Langues cibles ───────────────────────────────────────────────
LANGS_DESC = ["fr", "en", "de", "es", "ja"]   # langues pour descriptions + capacités
LANGS_INTL = {"en", "de", "es", "it", "ja", "ja-Hrkt", "ko", "zh-Hans", "zh-Hant"}

# ── Traductions ───────────────────────────────────────────────────
GEN_FR = {
    "generation-i":    "Génération I",
    "generation-ii":   "Génération II",
    "generation-iii":  "Génération III",
    "generation-iv":   "Génération IV",
    "generation-v":    "Génération V",
    "generation-vi":   "Génération VI",
    "generation-vii":  "Génération VII",
    "generation-viii": "Génération VIII",
    "generation-ix":   "Génération IX",
}

VERSION_FR = {
    "red": "Rouge", "blue": "Bleu", "yellow": "Jaune",
    "gold": "Or", "silver": "Argent", "crystal": "Cristal",
    "ruby": "Rubis", "sapphire": "Saphir", "emerald": "Émeraude",
    "firered": "Rouge Feu", "leafgreen": "Vert Feuille",
    "diamond": "Diamant", "pearl": "Perle", "platinum": "Platine",
    "heartgold": "Or HeartGold", "soulsilver": "Argent SoulSilver",
    "black": "Noir", "white": "Blanc",
    "black-2": "Noir 2", "white-2": "Blanc 2",
    "x": "X", "y": "Y",
    "omega-ruby": "Rubis Oméga", "alpha-sapphire": "Saphir Alpha",
    "sun": "Soleil", "moon": "Lune",
    "ultra-sun": "Ultra-Soleil", "ultra-moon": "Ultra-Lune",
    "lets-go-pikachu": "Pikachu", "lets-go-eevee": "Évoli",
    "sword": "Épée", "shield": "Bouclier",
    "brilliant-diamond": "Diamant Étincelant",
    "shining-pearl": "Perle Scintillante",
    "legends-arceus": "Légendes : Arceus",
    "scarlet": "Écarlate", "violet": "Violet",
}

HABITAT_FR = {
    "cave": "Grotte",
    "forest": "Forêt",
    "grassland": "Prairie",
    "mountain": "Montagne",
    "rare": "Rare",
    "rough-terrain": "Terrain accidenté",
    "sea": "Mer",
    "urban": "Urbain",
    "waters-edge": "Bord de l'eau",
}

# ── Charge les données existantes ────────────────────────────────
with open(DEST, encoding="utf-8") as f:
    meta = json.load(f)

# ── Cache évolutions ─────────────────────────────────────────────
evo_chain_cache = {}

def get_evo_chain(url):
    if url in evo_chain_cache:
        return evo_chain_cache[url]
    try:
        r = requests.get(url, timeout=10)
        chain = r.json()["chain"]
        result = parse_chain(chain)
        evo_chain_cache[url] = result
        time.sleep(0.2)
        return result
    except:
        return []

def parse_chain(node):
    result = []
    current = node["species"]["name"]
    evolutions = [e["species"]["name"] for e in node.get("evolves_to", [])]
    result.append({"slug": current, "evolves_to": evolutions})
    for child in node.get("evolves_to", []):
        result.extend(parse_chain(child))
    return result

def get_evolves_from(chain_data, slug):
    for entry in chain_data:
        if slug in entry["evolves_to"]:
            return entry["slug"]
    return None

def get_evolves_to(chain_data, slug):
    for entry in chain_data:
        if entry["slug"] == slug:
            return entry["evolves_to"]
    return []

# ── Cache talents ─────────────────────────────────────────────────
ability_cache = {}

def get_ability_i18n(slug):
    """Retourne {name_fr, desc_fr, name_en, desc_en, name_de, desc_de, name_es, desc_es, name_ja, desc_ja}"""
    if slug in ability_cache:
        return ability_cache[slug]
    result = {}
    for lang in LANGS_DESC:
        result[f"name_{lang}"] = slug
        result[f"desc_{lang}"] = ""
    try:
        r = requests.get(f"{API}/ability/{slug}", timeout=10)
        if r.status_code != 200:
            ability_cache[slug] = result
            return result
        d = r.json()
        # Noms par langue
        for n in d.get("names", []):
            lang = n["language"]["name"]
            if lang in LANGS_DESC:
                result[f"name_{lang}"] = n["name"]
        # Descriptions par langue (on prend la plus récente pour chaque langue)
        for entry in reversed(d.get("flavor_text_entries", [])):
            lang = entry["language"]["name"]
            if lang in LANGS_DESC and not result[f"desc_{lang}"]:
                result[f"desc_{lang}"] = entry["flavor_text"].replace("\n", " ").replace("\f", " ").strip()
        ability_cache[slug] = result
        time.sleep(0.2)
        return result
    except:
        ability_cache[slug] = result
        return result

def gender_label(rate):
    """Convertit gender_rate PokeAPI en % femelle lisible."""
    if rate == -1:
        return "Asexué"
    return round(rate / 8 * 100, 1)  # % femelle

# ── Enrichissement ────────────────────────────────────────────────
total = len(meta)
ok = 0
errors = []

print(f"🔍 Enrichissement de {total} Pokémon...\n")

for i, (name_fr, data) in enumerate(meta.items(), 1):
    # Saute si déjà enrichi avec toutes les langues
    if data.get("descriptions_fr") and data.get("descriptions_en"):
        ok += 1
        print(f"  [{i:3d}/{total}] ⏭  {name_fr} (déjà enrichi)")
        continue

    species_id = data.get("id", 0)
    if not species_id:
        errors.append(name_fr)
        continue

    try:
        # ── Appel 1 : /pokemon-species/{id}/ ──────────────────────
        # Pour les formes régionales (id > 10000 ou variantes), l'endpoint
        # /pokemon-species/ n'existe pas — on passe par /pokemon/{id}/
        # pour récupérer l'URL d'espèce de base, puis on l'appelle.
        r = requests.get(f"{API}/pokemon-species/{species_id}", timeout=10)
        if r.status_code != 200:
            # Fallback : récupère l'espèce via /pokemon/{id}/
            pr_fall = requests.get(f"{API}/pokemon/{species_id}", timeout=10)
            if pr_fall.status_code != 200:
                raise ValueError(f"HTTP {r.status_code} (species) et {pr_fall.status_code} (pokemon)")
            species_url = pr_fall.json().get("species", {}).get("url", "")
            if not species_url:
                raise ValueError("species URL introuvable dans /pokemon/")
            r = requests.get(species_url, timeout=10)
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code} (species fallback)")
            time.sleep(0.2)
        s = r.json()

        # Descriptions par jeu pour chaque langue
        # On indexe par le label de jeu en français (cohérence avec l'existant)
        # On collecte d'abord les versions FR pour établir le mapping version→label FR
        version_to_label_fr = {}
        for ft in s.get("flavor_text_entries", []):
            if ft["language"]["name"] == "fr":
                version = ft["version"]["name"]
                version_to_label_fr[version] = VERSION_FR.get(version, version)

        # Puis on collecte toutes les langues en utilisant ce mapping
        descriptions_by_lang = {lang: {} for lang in LANGS_DESC}
        desc_fr_last = ""
        for ft in s.get("flavor_text_entries", []):
            lang = ft["language"]["name"]
            if lang not in LANGS_DESC:
                continue
            version = ft["version"]["name"]
            text = ft["flavor_text"].replace("\n", " ").replace("\f", " ").strip()
            # Clé = label FR du jeu (ou slug si pas de traduction FR connue)
            label = version_to_label_fr.get(version, VERSION_FR.get(version, version))
            descriptions_by_lang[lang][label] = text
            if lang == "fr":
                desc_fr_last = text

        descriptions_fr = descriptions_by_lang["fr"]
        descriptions_en = descriptions_by_lang["en"]
        descriptions_de = descriptions_by_lang["de"]
        descriptions_es = descriptions_by_lang["es"]
        descriptions_ja = descriptions_by_lang["ja"]

        # Noms dans d'autres langues (SEO + fun)
        names_intl = {}
        for n in s.get("names", []):
            lang = n["language"]["name"]
            if lang in LANGS_INTL:
                names_intl[lang] = n["name"]
        # Alias pratique : nom anglais = nom le plus utile pour le SEO
        name_en = names_intl.get("en", "")

        # Catégories par langue
        categories: dict = {}
        for g in s.get("genera", []):
            lang = g["language"]["name"]
            if lang in LANGS_DESC:
                categories[lang] = g["genus"]
        category_fr = categories.get("fr", "")

        # Génération
        generation = GEN_FR.get(s.get("generation", {}).get("name", ""), "")

        # Taux de capture
        capture_rate = s.get("capture_rate", None)

        # Légendaire / Mythique
        is_legendary = s.get("is_legendary", False)
        is_mythical  = s.get("is_mythical", False)

        # Genre
        gender_rate = s.get("gender_rate", None)
        gender_fr   = gender_label(gender_rate) if gender_rate is not None else None

        # Habitat
        habitat_raw = s.get("habitat")
        habitat_fr  = HABITAT_FR.get(habitat_raw["name"], habitat_raw["name"]) if habitat_raw else None

        # Bonheur de base + éclosion
        base_happiness = s.get("base_happiness", None)
        hatch_counter  = s.get("hatch_counter", None)

        # Évolutions
        evo_url = s.get("evolution_chain", {}).get("url", "")
        chain   = get_evo_chain(evo_url) if evo_url else []
        slug_en = data.get("slug", "")
        # Pour les formes régionales le slug peut contenir "-hisui", "-paldea"...
        # On essaie d'abord le slug exact, puis le slug de base (sans suffixe de forme)
        evolves_from = get_evolves_from(chain, slug_en)
        evolves_to   = get_evolves_to(chain, slug_en)
        if not evolves_from and not evolves_to and "-" in slug_en:
            base_slug = slug_en.rsplit("-", 1)[0]
            evolves_from = get_evolves_from(chain, base_slug)
            evolves_to   = get_evolves_to(chain, base_slug)

        time.sleep(DELAY)

        # ── Appel 2 : /pokemon/{id}/ (pour les talents) ───────────
        abilities = []
        try:
            pr = requests.get(f"{API}/pokemon/{species_id}", timeout=10)
            if pr.status_code == 200:
                pdata = pr.json()
                for a in pdata.get("abilities", []):
                    ab_slug   = a["ability"]["name"]
                    is_hidden = a.get("is_hidden", False)
                    ab_info   = get_ability_i18n(ab_slug)
                    abilities.append({**ab_info, "is_hidden": is_hidden})
        except:
            pass

        # ── Mise à jour ───────────────────────────────────────────
        data["name_en"]         = name_en
        data["names_intl"]      = names_intl
        data["description_fr"]  = desc_fr_last
        data["descriptions_fr"] = descriptions_fr
        data["descriptions_en"] = descriptions_en
        data["descriptions_de"] = descriptions_de
        data["descriptions_es"] = descriptions_es
        data["descriptions_ja"] = descriptions_ja
        data["category_fr"]     = category_fr
        data["category_en"]     = categories.get("en", category_fr)
        data["category_de"]     = categories.get("de", category_fr)
        data["category_es"]     = categories.get("es", category_fr)
        data["category_ja"]     = categories.get("ja", category_fr)
        data["generation"]      = generation
        data["capture_rate"]    = capture_rate
        data["is_legendary"]    = is_legendary
        data["is_mythical"]     = is_mythical
        data["gender_fr"]       = gender_fr
        data["habitat_fr"]      = habitat_fr
        data["base_happiness"]  = base_happiness
        data["hatch_counter"]   = hatch_counter
        data["evolves_from"]    = evolves_from
        data["evolves_to"]      = evolves_to
        data["abilities"]       = abilities

        ok += 1
        flags = ("⭐" if is_legendary else "") + ("✨" if is_mythical else "")
        print(f"  [{i:3d}/{total}] ✅ {name_fr:20s} | {category_fr:20s} | {generation} {flags}")

    except Exception as e:
        errors.append(name_fr)
        print(f"  [{i:3d}/{total}] ❌ {name_fr}: {e}")

    time.sleep(DELAY)

    # Sauvegarde intermédiaire toutes les 50 entrées
    if i % 50 == 0:
        _tmp = DEST.with_suffix(".tmp")
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(_tmp, DEST)
        print(f"\n  💾 Sauvegarde intermédiaire ({i}/{total})\n")

# ── Sauvegarde finale atomique (évite la corruption du JSON) ──────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(_tmp, DEST)

print(f"\n{'='*55}")
print(f"✅ {ok}/{total} Pokémon enrichis")
if errors:
    print(f"❌ {len(errors)} erreurs : {errors[:10]}")
print(f"📄 Sauvegardé → {DEST}")
print(f"🎯 {len(ability_cache)} talents uniques mis en cache")
print("\nRelance npm run build pour rebuilder le site.")
