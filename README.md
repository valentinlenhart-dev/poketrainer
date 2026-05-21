# PokéNom — Site Astro

## Installation

```bash
cd site
npm install
npm run dev        # http://localhost:4321
npm run build      # génère dist/
npm run preview    # prévisualise le build
```

## Avant le premier build

```bash
# Générer le JSON enrichi depuis les données Python
python build-data.py
```

## Structure des pages générées

| Route | Pages | Priorité SEO |
|---|---|---|
| `/prenom/[prenom]` | 1 790 | ⭐⭐⭐ Priorité max |
| `/dresseur/[slug]` | 4 728 | ⭐⭐⭐ |
| `/top/legendaires` | 1 | ⭐⭐ |
| `/top/repandus` | 1 | ⭐⭐ |

## Déploiement Cloudflare Pages

1. Push sur GitHub
2. Connecter le repo dans Cloudflare Pages
3. Build command : `python build-data.py && npm run build`
4. Output directory : `dist`
5. Node version : 20+

## AdSense

Remplacer `ca-pub-XXXXXXXXXXXXXXXX` dans :
- `src/layouts/Base.astro`
- `src/components/AdSlot.astro`

Remplacer les `SLOT_*` dans les composants AdSlot par les IDs de tes emplacements.

## Prochaines pages à créer

- `src/pages/pokemon/[slug].astro` — 888 pages
- `src/pages/classe/[slug].astro` — 308 pages
- `src/pages/jeu/[slug].astro` — 17 pages
- `src/pages/lieu/[slug].astro` — 457 pages
- `src/pages/dresseurs-utilisant/[pokemon].astro` — 888 pages
