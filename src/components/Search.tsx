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

const MODAL_DURATION = 2600;
const NAV_DURATION   = 1500;
const AD_PUB         = 'ca-pub-6295830585093654';

const SEARCH_MESSAGES = [
  '🔍 Analyse du prénom…',
  '📚 Consultation des archives…',
  '⚡ Identification du dresseur…',
  '✅ Dresseur trouvé !',
];

const NAV_MESSAGES = [
  '📋 Chargement de la fiche…',
  '🎮 Récupération de l\'équipe Pokémon…',
  '✅ Prêt !',
];

// ── CSS partagé pour toutes les modales ────────────────────────────────────
const MODAL_CSS = `
  .modal-backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.55);
    backdrop-filter: blur(3px);
    z-index: 999;
    display: flex; align-items: center; justify-content: center;
    animation: modal-fade-in 0.2s ease;
  }
  @keyframes modal-fade-in { from { opacity:0 } to { opacity:1 } }

  .modal-card {
    background: var(--bg2);
    border: 1.5px solid var(--border);
    border-radius: var(--radius, 12px);
    box-shadow: 0 20px 60px rgba(0,0,0,.3);
    width: min(400px, 92vw);
    padding: 32px 28px 24px;
    display: flex; flex-direction: column; align-items: center; gap: 20px;
    animation: modal-slide-up 0.25s ease;
  }
  @keyframes modal-slide-up {
    from { transform: translateY(24px); opacity:0 }
    to   { transform: translateY(0);    opacity:1 }
  }

  .pokeball {
    width:64px; height:64px; border-radius:50%;
    border:4px solid var(--text,#1a1a1a);
    overflow:hidden; position:relative;
    animation: pokeball-spin 0.7s linear infinite; flex-shrink:0;
  }
  @keyframes pokeball-spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
  .pokeball__top    { position:absolute; inset:0 0 50% 0; background:var(--red,#dc2626); }
  .pokeball__bottom { position:absolute; inset:50% 0 0 0; background:#fff; }
  .pokeball__band   {
    position:absolute; top:calc(50% - 3px); left:-4px; right:-4px;
    height:6px; background:var(--text,#1a1a1a); z-index:2;
  }
  .pokeball__btn {
    position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    width:18px; height:18px; border-radius:50%;
    background:#fff; border:3px solid var(--text,#1a1a1a); z-index:3;
  }

  .modal-query {
    font-size:1.05rem; font-weight:800; color:var(--text); letter-spacing:-0.01em;
    text-align:center;
  }
  .modal-msg {
    font-size:0.88rem; color:var(--text-soft); min-height:1.4em; text-align:center;
  }
  .modal-progress-wrap {
    width:100%; height:4px; background:var(--border); border-radius:999px; overflow:hidden;
  }
  .modal-progress-bar {
    height:100%; background:var(--red,#dc2626); border-radius:999px; transition:width 0.05s linear;
  }
  .modal-ad {
    width:100%; min-height:90px;
    background:var(--bg,#f9f9f9);
    border:1px dashed var(--border);
    border-radius:var(--radius-sm,8px);
    overflow:hidden;
  }

  /* Share modal */
  .share-card {
    background: var(--bg2);
    border:1.5px solid var(--border);
    border-radius:var(--radius,12px);
    width:min(400px,92vw);
    padding:28px;
    display:flex; flex-direction:column; align-items:center; gap:18px;
    animation:modal-slide-up 0.25s ease;
    position:relative;
  }
  .share-close {
    position:absolute; top:12px; right:14px;
    background:none; border:none; cursor:pointer;
    font-size:1.1rem; color:var(--text-soft); line-height:1;
    padding:4px;
    transition:color .15s;
  }
  .share-close:hover { color:var(--text); }
  .share-rarity-big {
    font-size:2.8rem; line-height:1;
  }
  .share-name {
    font-size:1.4rem; font-weight:900; color:var(--text); text-align:center; line-height:1.2;
  }
  .share-label {
    font-size:0.82rem; color:var(--text-soft); text-align:center;
  }
  .share-divider {
    width:100%; height:1px; background:var(--border);
  }
  .share-actions {
    display:flex; gap:10px; flex-wrap:wrap; justify-content:center;
  }
  .share-btn {
    padding:9px 20px; border-radius:999px; border:1.5px solid var(--border);
    background:transparent; color:var(--text); cursor:pointer; font-size:0.85rem;
    font-weight:600; font-family:var(--font); transition:border-color .15s, background .15s;
  }
  .share-btn:hover { border-color:var(--border-focus); background:var(--bg); }
  .share-btn--primary {
    background:var(--red,#dc2626); color:#fff; border-color:transparent;
  }
  .share-btn--primary:hover { background:var(--red-dark,#b91c1c); }
  .share-btn--copied {
    background:var(--green,#16a34a) !important; border-color:transparent !important; color:#fff !important;
  }
`;

let modalCssInjected = false;
function ensureModalCss() {
  if (modalCssInjected || typeof document === 'undefined') return;
  const s = document.createElement('style');
  s.textContent = MODAL_CSS;
  document.head.appendChild(s);
  modalCssInjected = true;
}

function normalize(s: string): string {
  return s.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .trim();
}

// ── Composant AdSlot Preact ────────────────────────────────────────────────
function AdSlot({ slot }: { slot: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current || ref.current.querySelector('ins')) return;
    try {
      const ins = document.createElement('ins');
      ins.className = 'adsbygoogle';
      ins.style.cssText = 'display:block;width:100%;min-height:90px;';
      ins.setAttribute('data-ad-client', AD_PUB);
      ins.setAttribute('data-ad-slot', slot);
      ins.setAttribute('data-ad-format', 'auto');
      ins.setAttribute('data-full-width-responsive', 'true');
      ref.current.appendChild(ins);
      ((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({});
    } catch (_) {}
  }, []);
  return <div ref={ref} class="modal-ad" aria-hidden="true" />;
}

// ── Pokeball + barre de progression partagées ─────────────────────────────
function ProgressModal({
  title, messages, duration, slot, onDone, navTarget,
}: {
  title: string; messages: string[]; duration: number;
  slot: string; onDone: () => void; navTarget?: string;
}) {
  const [msgIdx, setMsgIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const startRef = useRef(performance.now());
  const rafRef   = useRef<number | null>(null);

  useEffect(() => {
    ensureModalCss();
  }, []);

  useEffect(() => {
    const tick = (now: number) => {
      const pct = Math.min(((now - startRef.current) / duration) * 100, 100);
      setProgress(pct);
      if (pct < 100) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [duration]);

  useEffect(() => {
    const step = duration / messages.length;
    const timers = messages.map((_, i) => setTimeout(() => setMsgIdx(i), i * step));
    return () => timers.forEach(clearTimeout);
  }, [duration]);

  useEffect(() => {
    const t = setTimeout(() => {
      onDone();
      if (navTarget) window.location.href = navTarget;
    }, duration);
    return () => clearTimeout(t);
  }, [duration, navTarget]);

  return (
    <div class="modal-backdrop" role="dialog" aria-modal="true" aria-label="Chargement">
      <div class="modal-card">
        <div class="pokeball" aria-hidden="true">
          <div class="pokeball__top" />
          <div class="pokeball__bottom" />
          <div class="pokeball__band" />
          <div class="pokeball__btn" />
        </div>
        <p class="modal-query">{title}</p>
        <p class="modal-msg">{messages[msgIdx]}</p>
        <div class="modal-progress-wrap">
          <div class="modal-progress-bar" style={{ width: `${progress}%` }} />
        </div>
        <AdSlot slot={slot} />
      </div>
    </div>
  );
}

// ── Modale partage ─────────────────────────────────────────────────────────
function ShareModal({
  query, count, rarityEmoji, rarityLabel, rarityKey, onClose,
}: {
  query: string; count: number; rarityEmoji: string;
  rarityLabel: string; rarityKey: string; onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => { ensureModalCss(); }, []);

  const shareText = count === 0
    ? `Mon prénom "${query}" n'existe chez aucun dresseur Pokémon — c'est unique ! 🌟 pokenom.fr`
    : count === 1
    ? `Mon prénom "${query}" n'appartient qu'à un seul dresseur légendaire ! 🏆 pokenom.fr`
    : `Il y a ${count} dresseurs Pokémon qui s'appellent "${query}" ${rarityEmoji} pokenom.fr`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(shareText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleNative = () => {
    if (navigator.share) {
      navigator.share({ text: shareText, url: `https://pokenom.fr/prenom/${normalize(query).replace(/\s+/g, '-')}` });
    } else {
      handleCopy();
    }
  };

  return (
    <div class="modal-backdrop" role="dialog" aria-modal="true" aria-label="Partager" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div class="share-card">
        <button class="share-close" onClick={onClose} aria-label="Fermer">✕</button>

        <div class="share-rarity-big"><img src={`/assets/rarity/${rarityKey}.svg`} alt="" width="48" height="48" /></div>
        <p class="share-name">"{query}"</p>
        <p class="share-label">
          {count === 0
            ? 'Prénom introuvable dans le monde Pokémon !'
            : count === 1
            ? '1 seul dresseur légendaire porte ce prénom'
            : `${count} dresseurs portent ce prénom · ${rarityLabel}`
          }
        </p>

        <div class="share-divider" />

        <AdSlot slot="2896100570" />

        <div class="share-divider" />

        <div class="share-actions">
          <button
            class={`share-btn share-btn--primary${copied ? ' share-btn--copied' : ''}`}
            onClick={handleCopy}
          >
            {copied ? '✓ Copié !' : '📋 Copier'}
          </button>
          {typeof navigator !== 'undefined' && 'share' in navigator && (
            <button class="share-btn" onClick={handleNative}>
              🔗 Partager
            </button>
          )}
          {count > 0 && (
            <a
              href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`}
              class="share-btn"
            >
              Voir la page →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Composant principal ────────────────────────────────────────────────────
export default function Search({ trainers }: SearchProps) {
  const [query,       setQuery]       = useState('');
  const [results,     setResults]     = useState<Trainer[]>([]);
  const [searched,    setSearched]    = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [highlightIdx,setHighlightIdx]= useState(-1);
  const [showSugg,    setShowSugg]    = useState(false);

  // Modales
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [pendingQuery,    setPendingQuery]    = useState('');
  const [navTarget,       setNavTarget]       = useState<string | null>(null);
  const [showShare,       setShowShare]       = useState(false);

  const inputRef  = useRef<HTMLInputElement>(null);
  const listRef   = useRef<HTMLUListElement>(null);
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
      normalize(t.name).includes(nq) ||
      normalize((t as any).name_normalized ?? t.name).includes(nq)
    );
    setResults(found);
    setSearched(true);
    setShowSugg(false);
    setSuggestions([]);
    setHighlightIdx(-1);
  }, [trainers]);

  // Ouvrir la modale de recherche
  const openSearchModal = useCallback((q: string) => {
    const effective = (highlightIdx >= 0 && suggestions[highlightIdx])
      ? suggestions[highlightIdx] : q;
    if (!normalize(effective)) return;
    setQuery(effective);
    setPendingQuery(effective);
    setShowSugg(false);
    setShowSearchModal(true);
  }, [highlightIdx, suggestions]);

  const handleSearchDone = useCallback(() => {
    setShowSearchModal(false);
    doSearch(pendingQuery);
  }, [pendingQuery, doSearch]);

  // Clic sur un résultat → interstitiel
  const handleResultClick = useCallback((e: MouseEvent, href: string) => {
    e.preventDefault();
    setNavTarget(href);
  }, []);

  const handleNavDone = useCallback(() => {
    // navigation gérée dans ProgressModal via window.location.href
  }, []);

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
    openSearchModal(query);
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
    openSearchModal(name);
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (highlightIdx >= 0 && listRef.current) {
      const item = listRef.current.children[highlightIdx] as HTMLElement;
      item?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightIdx]);

  const count      = results.length;
  const rarityKey  = count === 0 ? 'unique'    : count === 1 ? 'legendaire' : count <= 3 ? 'rare' : count <= 10 ? 'repandu' : 'partout';
  const rarityEmoji= count === 0 ? '✨'         : count === 1 ? '🏆'         : count <= 3 ? '💜'  : count <= 10 ? '👀'      : '🔥';
  const rarityLabel= count === 0 ? 'Introuvable': count === 1 ? 'Légendaire' : count <= 3 ? 'Rare': count <= 10 ? 'Répandu' : 'Partout !';

  return (
    <div class="search-island">

      {/* ── Modale recherche (2.6s) ── */}
      {showSearchModal && (
        <ProgressModal
          title={`"${pendingQuery}"`}
          messages={SEARCH_MESSAGES}
          duration={MODAL_DURATION}
          slot="2896100570"
          onDone={handleSearchDone}
        />
      )}

      {/* ── Modale navigation (1.5s) ── */}
      {navTarget && (
        <ProgressModal
          title="Chargement de la fiche…"
          messages={NAV_MESSAGES}
          duration={NAV_DURATION}
          slot="2896100570"
          onDone={handleNavDone}
          navTarget={navTarget}
        />
      )}

      {/* ── Modale partage ── */}
      {showShare && (
        <ShareModal
          query={query}
          count={count}
          rarityEmoji={rarityEmoji}
          rarityLabel={rarityLabel}
          rarityKey={rarityKey}
          onClose={() => setShowShare(false)}
        />
      )}

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

          {showSugg && suggestions.length > 0 && (
            <ul
              id="autocomplete-list"
              ref={listRef}
              class="autocomplete-list"
              role="listbox"
              onMouseDown={(e) => e.preventDefault()}
            >
              {suggestions.map((name, idx) => {
                const nn = normalize(name);
                const nq = normalize(query);
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
              key={h}
              type="button"
              class="hint-chip"
              onClick={() => { setQuery(h); openSearchModal(h); }}
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
              <img src={`/assets/rarity/${rarityKey}.svg`} alt="" width="14" height="14" style="vertical-align:middle;margin-right:4px;" /> {rarityLabel}
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

          {/* Bouton partager */}
          <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
            <button
              class="hint-chip"
              style="font-size:0.8rem;"
              onClick={() => setShowShare(true)}
            >
              🎉 Partager mon résultat
            </button>
          </div>

          {count > 0 && (
            <ul class="results-list" role="list">
              {results.slice(0, 3).map(t => (
                <li key={t.slug}>
                  <a
                    href={`/dresseur/${t.slug}`}
                    class="result-item"
                    onClick={(e) => handleResultClick(e as MouseEvent, `/dresseur/${t.slug}`)}
                  >
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

              {/* ── Ad inline après le 3e résultat ── */}
              {count > 3 && (
                <li aria-hidden="true" style="list-style:none;">
                  <InlineAd />
                </li>
              )}

              {results.slice(3, 8).map(t => (
                <li key={t.slug}>
                  <a
                    href={`/dresseur/${t.slug}`}
                    class="result-item"
                    onClick={(e) => handleResultClick(e as MouseEvent, `/dresseur/${t.slug}`)}
                  >
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

// ── Ad inline résultats ───────────────────────────────────────────────────
function InlineAd() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current || ref.current.querySelector('ins')) return;
    try {
      const ins = document.createElement('ins');
      ins.className = 'adsbygoogle';
      ins.style.cssText = 'display:block;width:100%;min-height:60px;';
      ins.setAttribute('data-ad-client', AD_PUB);
      ins.setAttribute('data-ad-slot', '9395123375');
      ins.setAttribute('data-ad-format', 'fluid');
      ins.setAttribute('data-ad-layout', 'in-article');
      ins.setAttribute('data-full-width-responsive', 'true');
      ref.current.appendChild(ins);
      ((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({});
    } catch (_) {}
  }, []);
  return (
    <div
      ref={ref}
      style="width:100%;min-height:60px;border-radius:var(--radius-sm,8px);overflow:hidden;background:var(--bg);border:1px dashed var(--border);"
      aria-hidden="true"
    />
  );
}
