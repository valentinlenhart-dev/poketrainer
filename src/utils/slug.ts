/**
 * Convertit un nom de Pokémon français en slug URL.
 * "Goélise" → "goelise"
 * "M. Mime"  → "m-mime"
 * "Nidoran♀" → "nidoran-f"
 */
export function toPokemonSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/♀/g, '-f')
    .replace(/♂/g, '-m')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')   // retire tous les diacritiques (é→e, ê→e…)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/**
 * Convertit un slug de lieu en libellé affichable en titre français.
 * "route-30"           → "Route 30"
 * "bois-de-la-nuit"   → "Bois de la Nuit"
 * "academie-pokemon"  → "Academie Pokémon"   (accents perdus à la slugification)
 *
 * Règle : première lettre du premier mot + chaque mot non-article en majuscule.
 * Articles français maintenus en minuscule : de, du, des, d, la, le, les, l, un, une, en, et, au, aux.
 */
const FR_ARTICLES = new Set(['de','du','des','d','la','le','les','l','un','une','en','et','au','aux','sur','sous','dans','par','pour']);

export function placeLabel(slug: string): string {
  if (!slug) return '';
  return slug
    .replace(/-/g, ' ')
    .split(' ')
    .map((word, i) => {
      if (!word) return word;
      if (i > 0 && FR_ARTICLES.has(word.toLowerCase())) return word.toLowerCase();
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
}
