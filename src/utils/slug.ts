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
