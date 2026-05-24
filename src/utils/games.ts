/**
 * Ordre de sortie chronologique des jeux présents dans trainers.json
 * et labels d'affichage normalisés.
 */

/** Slug de jeu → position dans l'ordre de sortie (plus bas = plus ancien) */
export const GAME_ORDER: Record<string, number> = {
  'or-et-argent':                                   1,  // 2000
  'cristal':                                        2,  // 2001
  'rubis-saphir':                                   3,  // 2003
  'colosseum':                                      4,  // 2003
  'rouge-feu-vert-feuille':                         5,  // 2004
  'xd-le-souffle-des-tenebres':                     6,  // 2005
  'emeraude':                                       7,  // 2005
  'diamant-perle':                                  8,  // 2007
  'platine':                                        9,  // 2008
  'heartgold-soulsilver':                           10, // 2010
  'noir-et-blanc':                                  11, // 2011
  'noir-2-et-blanc-2':                              12, // 2012
  'x-et-y':                                         13, // 2013
  'rubis-omega-saphir-alpha':                       14, // 2014
  'soleil-et-lune':                                 15, // 2016
  'ultra-soleil-et-ultra-lune':                     16, // 2017
  'let-s-go-pikachu-et-evoli':                      17, // 2018
  'epee-et-bouclier':                               18, // 2019
  'diamant-etincelant-et-perle-scintillante':       19, // 2021
  'ecarlate-et-violet':                             20, // 2022
};

/**
 * Slug de jeu → label court affiché dans les filtres et listes.
 * Si absent, on affiche le nom complet (avec "Pokémon").
 */
export const GAME_LABELS: Record<string, string> = {
  'or-et-argent':                                   'Pokémon Or / Argent',
  'cristal':                                        'Pokémon Cristal',
  'rubis-saphir':                                   'Pokémon Rubis / Saphir',
  'colosseum':                                      'Pokémon Colosseum',
  'rouge-feu-vert-feuille':                         'Pokémon Rouge Feu / Vert Feuille',
  'xd-le-souffle-des-tenebres':                     'Pokémon XD',
  'emeraude':                                       'Pokémon Émeraude',
  'diamant-perle':                                  'Pokémon Diamant / Perle',
  'platine':                                        'Pokémon Platine',
  'heartgold-soulsilver':                           'Pokémon HeartGold / SoulSilver',
  'noir-et-blanc':                                  'Pokémon Noir / Blanc',
  'noir-2-et-blanc-2':                              'Pokémon Noir 2 / Blanc 2',
  'x-et-y':                                         'Pokémon X / Y',
  'rubis-omega-saphir-alpha':                       'Pokémon Rubis Oméga / Saphir Alpha',
  'soleil-et-lune':                                 'Pokémon Soleil / Lune',
  'ultra-soleil-et-ultra-lune':                     'Pokémon Ultra-Soleil / Ultra-Lune',
  'let-s-go-pikachu-et-evoli':                      'Pokémon Let\'s Go Pikachu / Évoli',
  'epee-et-bouclier':                               'Pokémon Épée / Bouclier',
  'diamant-etincelant-et-perle-scintillante':       'Pokémon Diamant Étincelant / Perle Scintillante',
  'ecarlate-et-violet':                             'Pokémon Écarlate / Violet',
};

/** Convertit un nom de jeu en slug (même logique que le reste du site) */
export function toGameSlug(game: string): string {
  return game
    .replace('Pokémon ', '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/** Trie un tableau de noms de jeux par ordre de sortie */
export function sortGamesByRelease(games: string[]): string[] {
  return [...games].sort((a, b) => {
    const slugA = toGameSlug(a);
    const slugB = toGameSlug(b);
    return (GAME_ORDER[slugA] ?? 99) - (GAME_ORDER[slugB] ?? 99);
  });
}

/** Retourne le label d'affichage pour un nom de jeu */
export function gameLabel(game: string): string {
  const slug = toGameSlug(game);
  return GAME_LABELS[slug] ?? game;
}

/**
 * Ordre chronologique des versions individuelles utilisées comme clés
 * dans descriptions_fr de pokemon-meta.json (noms courts PokéAPI en français).
 */
export const POKEDEX_VERSION_ORDER: Record<string, number> = {
  // Gen 1 (1996)
  'Rouge': 1, 'Bleu': 2, 'Jaune': 3,
  // Gen 2 (2000)
  'Or': 4, 'Argent': 5, 'Cristal': 6,
  // Gen 3 (2003–2004)
  'Rubis': 7, 'Saphir': 8, 'Rouge Feu': 9, 'Vert Feuille': 10, 'Émeraude': 11,
  // Gen 4 (2007–2008)
  'Diamant': 12, 'Perle': 13, 'Platine': 14,
  // Gen 4 remakes (2010)
  'Or HeartGold': 15, 'Argent SoulSilver': 16,
  // Gen 5 (2011–2012)
  'Noir': 17, 'Blanc': 18, 'Noir 2': 19, 'Blanc 2': 20,
  // Gen 6 (2013–2014)
  'X': 21, 'Y': 22, 'Rubis Oméga': 23, 'Saphir Alpha': 24,
  // Gen 7 (2016–2017)
  'Soleil': 25, 'Lune': 26, 'Ultra-Soleil': 27, 'Ultra-Lune': 28,
  // Let's Go (2018)
  'Pikachu': 29, 'Évoli': 30,
  // Gen 8 (2019–2021)
  'Épée': 31, 'Bouclier': 32,
  'Diamant Étincelant': 33, 'Perle Scintillante': 34, 'Légendes : Arceus': 35,
  // Gen 9 (2022)
  'Écarlate': 36, 'Violet': 37,
};

/** Trie les entrées [version, desc] d'un objet descriptions_fr par date de sortie */
export function sortPokedexEntries(entries: [string, string][]): [string, string][] {
  return [...entries].sort(([a], [b]) =>
    (POKEDEX_VERSION_ORDER[a] ?? 99) - (POKEDEX_VERSION_ORDER[b] ?? 99)
  );
}
