/** Search.tsx — Island Preact — recherche client-side depuis le JSON statique */
import { useState, useCallback, useRef } from 'preact/hooks';

interface Trainer {
  slug: string;
  name: string;
  class: string;
  game: string;
  place?: string;
  team?: string[];
  rarity_emoji: string;
  rarity_label: string;
  rarity_key: string;
  name_count: number;
}

interface SearchProps {
  trainers: Trainer[];
}

const HINTS = ['Valentin', 'Pierre', 'Cynthia', 'Lance', 'Iris', 'Leon', 'Marie'];

function normalize(s: string): string {
  return s.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .trim();
}

function RarityBadge({ rarity_key, rarity_emoji, rarity_label }: Pick<Trainer, 'rarity_key' | 'rarity_emoji' | 'rarity_label'>) {
  return (
    <span class={`rarity rarity--${rarity_key}`}>
      {rarity_emoji} {rarity_label}
    </span>
  );
}

export default function Search({ trainers }: SearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Trainer[]>([]);
  const [searched, setSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const doSearch = useCallback((q: string) => {
    const nq = normalize(q);
    if (!nq) return;
    const found = trainers.filter(t =>
      normalize(t.name).includes(nq) || normalize(t.name_normalized ?? t.name).includes(nq)
    );
    setResults(found);
    setSearched(true);
  }, [trainers]);

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    doSearch(query);
  };

  const count = results.length;
  const rarityKey = count === 0 ? 'unique' : count === 1 ? 'legendaire' : count <= 3 ? 'rare' : count <= 10 ? 'repandu' : 'partout';
  const rarityEmoji = count === 0 ? '✨' : count === 1 ? '🏆' : count <= 3 ? '💜' : count <= 10 ? '👀' : '🔥';
  const rarityLabel = count === 0 ? 'Introuvable' : count === 1 ? 'Légendaire' : count <= 3 ? 'Rare' : count <= 10 ? 'Répandu' : 'Partout !';

  return (
    <div class="search-island">
      <form onSubmit={handleSubmit} class="search-form" role="search">
        <div class="search-input-wrap">
          <label for="search-q" class="sr-only">Rechercher un prénom</label>
          <input
            id="search-q"
            ref={inputRef}
            type="search"
            value={query}
            onInput={(e) => setQuery((e.target as HTMLInputElement).value)}
            placeholder="Ton prénom ou celui d'un ami…"
            autocomplete="off"
            spellcheck={false}
            maxLength={40}
            class="search-input"
            aria-label="Entrer un prénom"
          />
          <button type="submit" class="search-btn" aria-label="Rechercher">
            Trouver mon dresseur ⚡
          </button>
        </div>
        <div class="search-hints" aria-label="Suggestions rapides">
          {HINTS.map(h => (
            <button
              type="button"
              class="hint-chip"
              onClick={() => { setQuery(h); doSearch(h); }}
            >
              {h}
            </button>
          ))}
        </div>
      </form>

      {searched && (
        <div class="search-results" role="region" aria-live="polite" aria-label="Résultats">
          <div class="results-header">
            <span class={`rarity rarity--${rarityKey}`}>
              {rarityEmoji} {rarityLabel}
            </span>
            <p class="results-count">
              {count === 0
                ? `Aucun dresseur ne s'appelle "${query}" — c'est unique au monde !`
                : count === 1
                ? `1 seul dresseur légendaire s'appelle "${query}" !`
                : `${count} dresseurs s'appellent "${query}"`
              }
            </p>
            {count > 0 && (
              <a href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`} class="see-page-link">
                Voir la page complète →
              </a>
            )}
          </div>

          {count > 0 && (
            <ul class="results-list" role="list">
              {results.slice(0, 8).map(t => (
                <li key={t.slug}>
                  <a href={`/dresseur/${t.slug}`} class="result-item">
                    <div class="result-item__left">
                      <span class="result-class">{t.class}</span>
                      <strong class="result-name">{t.name}</strong>
                    </div>
                    <div class="result-item__right">
                      <span class="result-game">{t.game.replace('Pokémon ', '')}</span>
                      {t.team && t.team.length > 0 && (
                        <span class="result-team">{t.team.slice(0, 3).join(', ')}{t.team.length > 3 ? '…' : ''}</span>
                      )}
                    </div>
                    <span class="result-arrow">→</span>
                  </a>
                </li>
              ))}
              {count > 8 && (
                <li>
                  <a href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`} class="see-all-link">
                    Voir les {count} dresseurs →
                  </a>
                </li>
              )}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
