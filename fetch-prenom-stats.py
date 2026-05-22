#!/usr/bin/env python3
"""
fetch-prenom-stats.py — Statistiques INSEE des prénoms français

Télécharge le fichier "Fichier des prénoms" de l'INSEE (données ouvertes)
et génère src/data/prenom-stats.json avec, pour chaque prénom présent
dans trainers.json :
  total       — total des naissances depuis 1900
  total_m     — dont garçons
  total_f     — dont filles
  pic_annee   — année avec le plus de naissances
  pic_count   — nombre de naissances cette année-là
  par_an      — liste [{an, n}] pour le graphique (1950+)

Lance : python fetch-prenom-stats.py
Durée : ~30 secondes (1 téléchargement + parsing local)
"""
import json, io, zipfile, csv, unicodedata
from pathlib import Path
from collections import defaultdict

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    import sys; sys.exit(1)

# ── Chemins ──────────────────────────────────────────────────────
ROOT      = Path(__file__).parent
TRAINERS  = ROOT / "src" / "data" / "trainers.json"
DEST      = ROOT / "src" / "data" / "prenom-stats.json"

# ── URL INSEE (données ouvertes, mise à jour annuelle) ───────────
# Fichier des prénoms — édition 2023
INSEE_URL = "https://www.insee.fr/fr/statistiques/fichier/7633685/nat2023_csv.zip"
# Fallback data.gouv.fr si INSEE inaccessible
DATAGOUV_URL = "https://www.data.gouv.fr/fr/datasets/r/0e5b34b7-7a63-47fb-a3ab-a5b42e48eaca"

def normalize(name: str) -> str:
    """Minuscule + suppression accents pour comparaison."""
    return unicodedata.normalize("NFD", name.lower()).encode("ascii", "ignore").decode()

# ── Charge les prénoms des dresseurs ─────────────────────────────
with open(TRAINERS, encoding="utf-8") as f:
    trainers = json.load(f)

# Index : slug_normalisé → nom_affiché  (ex: "sacha" → "Sacha")
trainer_names: dict[str, str] = {}
for t in trainers:
    name = t.get("name", "")
    slug = t.get("name_slug", normalize(name))
    trainer_names[slug] = name

print(f"📋 {len(trainer_names)} prénoms de dresseurs à rechercher\n")

# ── Téléchargement INSEE ──────────────────────────────────────────
print("⬇️  Téléchargement du fichier INSEE...")
csv_content = None

for url in [INSEE_URL, DATAGOUV_URL]:
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        # Le fichier peut être un ZIP ou un CSV direct
        if r.headers.get("content-type", "").startswith("application/zip") or url.endswith(".zip"):
            z = zipfile.ZipFile(io.BytesIO(r.content))
            csv_name = next(n for n in z.namelist() if n.endswith(".csv"))
            csv_content = z.read(csv_name).decode("utf-8")
        else:
            csv_content = r.text
        print(f"   ✅ Téléchargé depuis {url.split('/')[2]}")
        break
    except Exception as e:
        print(f"   ⚠️  Échec {url.split('/')[2]}: {e}")

if not csv_content:
    print("❌ Impossible de télécharger les données INSEE. Vérifiez votre connexion.")
    import sys; sys.exit(1)

# ── Parsing ───────────────────────────────────────────────────────
print("🔍 Parsing du CSV INSEE...")

# Structure : sexe;preusuel;annais;nombre
# sexe: 1=M 2=F | annais: "XXXX" = inconnu | nombre: "_" = < seuil (3)

# stats[slug_normalisé] = {m: {annee: count}, f: {annee: count}}
stats: dict[str, dict] = defaultdict(lambda: {"m": defaultdict(int), "f": defaultdict(int)})

# Normalisation de tous les slugs de dresseurs pour comparaison
trainer_slugs_norm = {normalize(k): k for k in trainer_names}

reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
rows_read = 0
rows_matched = 0

for row in reader:
    rows_read += 1
    raw_name = row.get("preusuel", "").strip()
    if raw_name in ("_PRENOMS_RARES", ""):
        continue

    annais = row.get("annais", "XXXX").strip()
    if annais == "XXXX":
        continue

    nombre_raw = row.get("nombre", "_").strip()
    if nombre_raw in ("_", ""):
        continue

    try:
        annee  = int(annais)
        nombre = int(nombre_raw)
        sexe   = row.get("sexe", "1").strip()
    except ValueError:
        continue

    # Normalise le prénom INSEE → compare avec nos slugs
    norm_insee = normalize(raw_name)
    if norm_insee not in trainer_slugs_norm:
        continue

    slug = trainer_slugs_norm[norm_insee]
    gender = "m" if sexe == "1" else "f"
    stats[slug]["m" if sexe == "1" else "f"][annee] += nombre
    rows_matched += 1

print(f"   {rows_read:,} lignes lues, {rows_matched:,} lignes correspondantes")

# ── Agrégation ────────────────────────────────────────────────────
print("📊 Agrégation des données...")

output: dict[str, dict] = {}

for slug, genders in stats.items():
    all_years: dict[int, int] = defaultdict(int)
    total_m = 0
    total_f = 0

    for annee, count in genders["m"].items():
        all_years[annee] += count
        total_m += count
    for annee, count in genders["f"].items():
        all_years[annee] += count
        total_f += count

    if not all_years:
        continue

    pic_annee = max(all_years, key=lambda a: all_years[a])
    pic_count = all_years[pic_annee]
    total     = total_m + total_f

    # Sparkline : toutes les décennies depuis 1950
    par_an = [
        {"an": an, "n": all_years[an]}
        for an in sorted(all_years)
        if an >= 1950
    ]

    output[slug] = {
        "total":     total,
        "total_m":   total_m,
        "total_f":   total_f,
        "pic_annee": pic_annee,
        "pic_count": pic_count,
        "par_an":    par_an,
    }

# ── Sauvegarde ────────────────────────────────────────────────────
with open(DEST, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

print(f"\n{'='*55}")
print(f"✅ {len(output)} prénoms avec données INSEE")
missing = [k for k in trainer_names if k not in output]
print(f"⚪ {len(missing)} prénoms sans données (rares ou absents du fichier INSEE)")
if missing[:10]:
    print(f"   Ex: {', '.join(missing[:10])}")
print(f"📄 Sauvegardé → {DEST}")
print("\nRelance npm run build pour rebuilder le site.")
