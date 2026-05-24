#!/usr/bin/env python3
"""
Fusionne les trainers scrapés (XD, Colosseum, LetsGo) dans trainers.json principal.
Génère les champs manquants : slug, class_slug, game_slug, place_slug,
name_count, rarity_key/emoji/label/desc.
"""
import json, re, unicodedata, shutil
from pathlib import Path
from collections import Counter

SITE = Path(__file__).parent
DATA = SITE / 'src' / 'data'
SCRAPERS = SITE.parent / 'scrapers'

# ── Slugification ──────────────────────────────────────────────
def slugify(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

# ── Mapping game → game_slug ───────────────────────────────────
GAME_SLUG = {
    'Pokémon Or et Argent':                              'or-et-argent',
    'Pokémon Cristal':                                   'cristal',
    'Pokémon Rouge Feu Vert Feuille':                    'rouge-feu-vert-feuille',
    'Pokémon Rubis Saphir':                              'rubis-saphir',
    'Pokémon Émeraude':                                  'emeraude',
    'Pokémon Diamant Perle':                             'diamant-perle',
    'Pokémon Platine':                                   'platine',
    'Pokémon HeartGold SoulSilver':                      'heartgold-soulsilver',
    'Pokémon Noir et Blanc':                             'noir-et-blanc',
    'Pokémon Noir 2 et Blanc 2':                         'noir-2-et-blanc-2',
    'Pokémon X et Y':                                    'x-et-y',
    'Pokémon Rubis Oméga Saphir Alpha':                  'rubis-omega-saphir-alpha',
    'Pokémon Soleil et Lune':                            'soleil-et-lune',
    'Pokémon Ultra-Soleil et Ultra-Lune':                'ultra-soleil-et-ultra-lune',
    'Pokémon Épée et Bouclier':                          'epee-et-bouclier',
    'Pokémon Diamant Étincelant et Perle Scintillante':  'diamant-etincelant-et-perle-scintillante',
    'Pokémon Écarlate et Violet':                        'ecarlate-et-violet',
    # Nouveaux
    'Pokémon Colosseum':                                 'colosseum',
    'Pokémon XD : Le Souffle des Ténèbres':              'xd',
    "Pokémon Let's Go, Pikachu et Évoli":                'letsgo',
}

# ── Rarity ────────────────────────────────────────────────────
def rarity(count):
    if count == 1:
        return ('legendaire', '🏆', 'Légendaire', 'Un seul dresseur légendaire porte ce prénom !')
    elif count <= 3:
        return ('rare', '💜', 'Rare', 'Ce prénom est assez rare dans le monde Pokémon.')
    elif count <= 10:
        return ('repandu', '👀', 'Répandu', 'Plusieurs dresseurs portent ce prénom.')
    else:
        return ('partout', '🔥', 'Partout !', 'Ce prénom est très populaire chez les dresseurs !')

# ── Load ───────────────────────────────────────────────────────
with open(DATA / 'trainers.json', encoding='utf-8') as f:
    main = json.load(f)

new_batches = []
for game in ['colosseum', 'xd', 'letsgo']:
    path = SCRAPERS / game / 'trainers.json'
    with open(path, encoding='utf-8') as f:
        new_batches.extend(json.load(f))

print(f'Existants : {len(main)}')
print(f'Nouveaux  : {len(new_batches)} (Colosseum + XD + LetsGo)')

# Vérifier qu'il n'y a pas de collision d'IDs
existing_ids = {t['id'] for t in main}
new_ids = {t['id'] for t in new_batches}
collisions = existing_ids & new_ids
if collisions:
    print(f'⚠️  Collisions IDs : {sorted(collisions)[:10]}')
else:
    print('✅ Pas de collision d\'IDs')

# ── Calcul name_count global (sur l'ensemble fusionné) ─────────
all_names = [t['name_normalized'] for t in main] + \
            [t['name_normalized'] for t in new_batches]
name_counts = Counter(all_names)

# ── Recalculer rarity pour les trainers existants ─────────────
# (leurs name_count peut changer avec les nouveaux noms)
updated_main = []
for t in main:
    nc = name_counts[t['name_normalized']]
    rk, re_, rl, rd = rarity(nc)
    t2 = dict(t)
    t2['name_count']   = nc
    t2['rarity_key']   = rk
    t2['rarity_emoji'] = re_
    t2['rarity_label'] = rl
    t2['rarity_desc']  = rd
    updated_main.append(t2)

# ── Générer les champs manquants pour les nouveaux ────────────
# Slugs déjà utilisés pour éviter les doublons
used_slugs = {t['slug'] for t in updated_main}

enriched_new = []
for t in new_batches:
    game_slug = GAME_SLUG.get(t['game'])
    if not game_slug:
        print(f'  ⚠️  Jeu inconnu : {t["game"]!r}')
        game_slug = slugify(t['game'])

    name_slug  = t['name_normalized']
    class_slug = slugify(t['class'])
    place_slug = t['place']  # déjà slugifié par le scraper

    # Slug de base : class-name-game
    base_slug = f'{class_slug}-{name_slug}-{game_slug}'
    slug = base_slug

    # Si collision, ajouter le lieu
    if slug in used_slugs:
        slug = f'{base_slug}-{place_slug}'
    # Si toujours collision (rare), ajouter l'id
    if slug in used_slugs:
        slug = f'{base_slug}-{t["id"]}'

    used_slugs.add(slug)

    nc = name_counts[name_slug]
    rk, re_, rl, rd = rarity(nc)

    enriched_new.append({
        'id':            t['id'],
        'name':          t['name'],
        'name_normalized': name_slug,
        'class':         t['class'],
        'team':          t['team'],
        'place':         t['place'],
        'game':          t['game'],
        'slug':          slug,
        'name_slug':     name_slug,
        'class_slug':    class_slug,
        'game_slug':     game_slug,
        'place_slug':    place_slug,
        'rarity_key':    rk,
        'rarity_emoji':  re_,
        'rarity_label':  rl,
        'rarity_desc':   rd,
        'name_count':    nc,
    })

# ── Fusionner et trier par id ──────────────────────────────────
merged = sorted(updated_main + enriched_new, key=lambda x: x['id'])

# ── Backup + save ──────────────────────────────────────────────
backup = DATA / 'trainers_before_merge.json'
if not backup.exists():
    shutil.copy(DATA / 'trainers.json', backup)
    print(f'💾 Backup → {backup.name}')

out = DATA / 'trainers.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f'\n✅ Fusionné : {len(merged)} dresseurs → {out}')
print(f'   Dont nouveaux : {len(enriched_new)}')
print()

# ── Stats ──────────────────────────────────────────────────────
from collections import Counter as C
games = C(t['game'] for t in merged)
print('Par jeu :')
for g, c in sorted(games.items(), key=lambda x: -x[1]):
    print(f'  {c:4d}  {g}')

print()
rarity_dist = C(t['rarity_key'] for t in merged)
print('Distribution rarity :', dict(rarity_dist))

# Vérifier slugs dupliqués
slug_dupes = {s: c for s, c in C(t['slug'] for t in merged).items() if c > 1}
print(f'Slugs dupliqués : {len(slug_dupes)}', slug_dupes if slug_dupes else '')
