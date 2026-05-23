/** Search.tsx — Island Preact — recherche client-side depuis le JSON statique */
import { useState, useCallback, useRef, useMemo, useEffect } from 'preact/hooks';

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

export default function Search({ trainers }: SearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Trainer[]>([]);
  const [searched, setSearched] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [highlightIdx, setHighlightIdx] = useState(-1);
  const [showSugg, setShowSugg] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Prénoms uniques triés — calculé une seule fois
  const uniqueNames = useMemo(() => {
    const s = new Set(trainers.map(t => t.name));
    return [...s].sort((a, b) => a.localeCompare(b, 'fr'));
  }, [trainers]);

  const doSearch = useCallback((q: string) => {
    const nq = normalize(q);
    if (!nq) return;
    const found = trainers.filter(t =>
      normalize(t.name).includes(nq) || normalize((t as any).name_normalized ?? t.name).includes(nq)
    );
    setResults(found);
    setSearched(true);
    setShowSugg(false);
    setSuggestions([]);
    setHighlightIdx(-1);
  }, [trainers]);

  const handleInput = (e: Event) => {
    const val = (e.target as HTMLInputElement).value;
    setQuery(val);
    setHighlightIdx(-1);
    const nq = normalize(val);
    if (nq.length < 2) {
      setSuggestions([]);
      setShowSugg(false);
      return;
    }
    const matches = uniqueNames.filter(n => normalize(n).startsWith(nq)).slice(0, 7);
    setSuggestions(matches);
    setShowSugg(matches.length > 0);
  };

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    if (highlightIdx >= 0 && suggestions[highlightIdx]) {
      const sel = suggestions[highlightIdx];
      setQuery(sel);
      doSearch(sel);
    } else {
      doSearch(query);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (!showSugg || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIdx(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIdx(i => Math.max(i - 1, -1));
    } else if (e.key === 'Escape') {
      setShowSugg(false);
      setHighlightIdx(-1);
    }
  };

  const pickSuggestion = (name: string) => {
    setQuery(name);
    doSearch(name);
    inputRef.current?.focus();
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightIdx >= 0 && listRef.current) {
      const item = listRef.current.children[highlightIdx] as HTMLElement;
      item?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightIdx]);

  const count = results.length;
  const rarityKey = count === 0 ? 'unique' : count === 1 ? 'legendaire' : count <= 3 ? 'rare' : count <= 10 ? 'repandu' : 'partout';
  const rarityEmoji = count === 0 ? '✨' : count === 1 ? '🏆' : count <= 3 ? '💜' : count <= 10 ? '👀' : '🔥';
  const rarityLabel = count === 0 ? 'Introuvable' : count === 1 ? 'Légendaire' : count <= 3 ? 'Rare' : count <= 10 ? 'Répandu' : 'Partout !';

  return (
    <div class="search-island">
      <form onSubmit={handleSubmit} class="search-form" role="search">
        <div class="search-input-wrap" style="position:relative">
          <label for="search-q" class="sr-only">Rechercher un prénom</label>
          <input
            id="search-q"
            ref={inputRef}
            type="search"
            value={query}
            onInput={handleInput}
            onKeyDown={handleKeyDown}
            onFocus={() => { if (suggestions.length > 0) setShowSugg(true); }}
            onBlur={() => { blurTimer.current = setTimeout(() => setShowSugg(false), 150); }}
            placeholder="Ton prénom ou celui d'un ami…"
            autocomplete="off"
            spellcheck={false}
            maxLength={40}
            class="search-input"
            aria-label="Entrer un prénom"
            aria-autocomplete="list"
            aria-expanded={showSugg}
            aria-controls="autocomplete-list"
          />
          <button type="submit" class="search-btn" aria-label="Rechercher">
            Trouver mon dresseur ⚡
          </button>

          {/* Dropdown autocomplétion */}
          {showSugg && suggestions.length > 0 && (
            <ul
              id="autocomplete-list"
              ref={listRef}
              class="autocomplete-list"
              role="listbox"
              onMouseDown={(e) => e.preventDefault()}
            >
              {suggestions.map((name, idx) => {
                const nq = normalize(query);
                const nn = normalize(name);
                const matchStart = nn.indexOf(nq);
                return (
                  <li
                    key={name}
                    role="option"
                    aria-selected={idx === highlightIdx}
                    class={`autocomplete-item${idx === highlightIdx ? ' autocomplete-item--active' : ''}`}
                    onClick={() => pickSuggestion(name)}
                    onMouseEnter={() => setHighlightIdx(idx)}
                  >
                    {matchStart >= 0
                      ? <><span class="autocomplete-match">{name.slice(0, query.length)}</span>{name.slice(query.length)}</>
                      : name
                    }
                  </li>
                );
              })}
            </ul>
          )}
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
