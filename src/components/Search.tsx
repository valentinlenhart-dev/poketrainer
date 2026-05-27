/** Search.tsx — Island Preact — recherche client-side depuis le JSON statique */
import { useState, useCallback, useRef, useMemo, useEffect } from 'preact/hooks';
import trainerClassesRaw from '../data/trainer-classes-i18n.json';

const TC = trainerClassesRaw as Record<string, Record<string, string>>;

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
  pkmNames?: Record<string, Record<string, string>>;
}

const HINTS = ['Valentin', 'Pierre', 'Cynthia', 'Lance', 'Iris', 'Leon', 'Marie'];

const MODAL_DURATION = 2600;
const NAV_DURATION   = 1500;
const AD_PUB         = 'ca-pub-6295830585093654';

// ── Détection de la langue (même logique que Base.astro) ─────────────────────
function getLang(): string {
  if (typeof window === 'undefined') return 'fr';
  const saved = localStorage.getItem('pokenom_lang');
  if (saved) return saved;
  return document.documentElement.lang || 'fr';
}

// ── Dictionnaire i18n complet ────────────────────────────────────────────────
const SEARCH_I18N: Record<string, {
  searchMessages: string[];
  navMessages: string[];
  navTitle: string;
  labelSrOnly: string;
  placeholder: string;
  ariaInput: string;
  btnSearch: string;
  ariaResults: string;
  ariaLoading: string;
  ariaShare: string;
  ariaClose: string;
  count0: (q: string) => string;
  count1: (q: string) => string;
  countN: (n: number, q: string) => string;
  seeFullPage: string;
  shareBtn: string;
  seeAllTrainers: (n: number) => string;
  shareLbl0: string;
  shareLbl1: string;
  shareLblN: (n: number, lbl: string) => string;
  shareText0: (q: string) => string;
  shareText1: (q: string) => string;
  shareTextN: (n: number, q: string, emoji: string) => string;
  copy: string;
  copied: string;
  shareNative: string;
  viewPage: string;
  rarityLabels: Record<string, string>;
}> = {
  fr: {
    searchMessages: ['🔍 Analyse du prénom…','📚 Consultation des archives…','⚡ Identification du dresseur…','✅ Dresseur trouvé !'],
    navMessages: ['📋 Chargement de la fiche…','🎮 Récupération de l\'équipe Pokémon…','✅ Prêt !'],
    navTitle: 'Chargement de la fiche…',
    labelSrOnly: 'Rechercher un prénom',
    placeholder: 'Ton prénom ou celui d\'un ami…',
    ariaInput: 'Entrer un prénom',
    btnSearch: 'Trouver mon dresseur ⚡',
    ariaResults: 'Résultats',
    ariaLoading: 'Chargement',
    ariaShare: 'Partager',
    ariaClose: 'Fermer',
    count0: (q) => `Aucun dresseur ne s'appelle "${q}" — c'est unique au monde !`,
    count1: (q) => `1 seul dresseur légendaire s'appelle "${q}" !`,
    countN: (n, q) => `${n} dresseurs s'appellent "${q}"`,
    seeFullPage: 'Voir la page complète →',
    shareBtn: '🎉 Partager mon résultat',
    seeAllTrainers: (n) => `Voir les ${n} dresseurs →`,
    shareLbl0: 'Prénom introuvable dans le monde Pokémon !',
    shareLbl1: '1 seul dresseur légendaire porte ce prénom',
    shareLblN: (n, lbl) => `${n} dresseurs portent ce prénom · ${lbl}`,
    shareText0: (q) => `Mon prénom "${q}" n'existe chez aucun dresseur Pokémon — c'est unique ! 🌟 pokenom.fr`,
    shareText1: (q) => `Mon prénom "${q}" n'appartient qu'à un seul dresseur légendaire ! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `Il y a ${n} dresseurs Pokémon qui s'appellent "${q}" ${e} pokenom.fr`,
    copy: '📋 Copier',
    copied: '✓ Copié !',
    shareNative: '🔗 Partager',
    viewPage: 'Voir la page →',
    rarityLabels: { unique:'Introuvable', legendaire:'Légendaire', rare:'Rare', repandu:'Répandu', partout:'Partout !' },
  },
  en: {
    searchMessages: ['🔍 Analyzing the name…','📚 Consulting the archives…','⚡ Identifying the trainer…','✅ Trainer found!'],
    navMessages: ['📋 Loading the profile…','🎮 Fetching the Pokémon team…','✅ Ready!'],
    navTitle: 'Loading the profile…',
    labelSrOnly: 'Search for a name',
    placeholder: 'Your name or a friend\'s…',
    ariaInput: 'Enter a name',
    btnSearch: 'Find my trainer ⚡',
    ariaResults: 'Results',
    ariaLoading: 'Loading',
    ariaShare: 'Share',
    ariaClose: 'Close',
    count0: (q) => `No trainer is called "${q}" — it's one of a kind!`,
    count1: (q) => `Only 1 legendary trainer is named "${q}"!`,
    countN: (n, q) => `${n} trainers are named "${q}"`,
    seeFullPage: 'View full page →',
    shareBtn: '🎉 Share my result',
    seeAllTrainers: (n) => `View all ${n} trainers →`,
    shareLbl0: 'Name not found in the Pokémon world!',
    shareLbl1: 'Only 1 legendary trainer bears this name',
    shareLblN: (n, lbl) => `${n} trainers share this name · ${lbl}`,
    shareText0: (q) => `My name "${q}" doesn't exist in any Pokémon trainer — it's unique! 🌟 pokenom.fr`,
    shareText1: (q) => `My name "${q}" belongs to only one legendary trainer! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `There are ${n} Pokémon trainers named "${q}" ${e} pokenom.fr`,
    copy: '📋 Copy',
    copied: '✓ Copied!',
    shareNative: '🔗 Share',
    viewPage: 'View page →',
    rarityLabels: { unique:'Unfindable', legendaire:'Legendary', rare:'Rare', repandu:'Common', partout:'Everywhere!' },
  },
  de: {
    searchMessages: ['🔍 Name wird analysiert…','📚 Archive werden durchsucht…','⚡ Trainer wird identifiziert…','✅ Trainer gefunden!'],
    navMessages: ['📋 Profil wird geladen…','🎮 Pokémon-Team wird abgerufen…','✅ Bereit!'],
    navTitle: 'Profil wird geladen…',
    labelSrOnly: 'Nach einem Namen suchen',
    placeholder: 'Dein Name oder der eines Freundes…',
    ariaInput: 'Namen eingeben',
    btnSearch: 'Meinen Trainer finden ⚡',
    ariaResults: 'Ergebnisse',
    ariaLoading: 'Laden',
    ariaShare: 'Teilen',
    ariaClose: 'Schließen',
    count0: (q) => `Kein Trainer heißt „${q}“ — einzigartig auf der Welt!`,
    count1: (q) => `Nur 1 legendärer Trainer heißt „${q}“!`,
    countN: (n, q) => `${n} Trainer heißen „${q}“`,
    seeFullPage: 'Vollständige Seite →',
    shareBtn: '🎉 Ergebnis teilen',
    seeAllTrainers: (n) => `Alle ${n} Trainer ansehen →`,
    shareLbl0: 'Name in der Pokémon-Welt nicht gefunden!',
    shareLbl1: 'Nur 1 legendärer Trainer trägt diesen Namen',
    shareLblN: (n, lbl) => `${n} Trainer tragen diesen Namen · ${lbl}`,
    shareText0: (q) => `Mein Name „${q}“ gibt es bei keinem Pokémon-Trainer — einzigartig! 🌟 pokenom.fr`,
    shareText1: (q) => `Mein Name „${q}“ gehört nur einem legendären Trainer! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `Es gibt ${n} Pokémon-Trainer namens „${q}“ ${e} pokenom.fr`,
    copy: '📋 Kopieren',
    copied: '✓ Kopiert!',
    shareNative: '🔗 Teilen',
    viewPage: 'Seite ansehen →',
    rarityLabels: { unique:'Unbekannt', legendaire:'Legendär', rare:'Selten', repandu:'Verbreitet', partout:'Überall!' },
  },
  es: {
    searchMessages: ['🔍 Analizando el nombre…','📚 Consultando los archivos…','⚡ Identificando al entrenador…','✅ ¡Entrenador encontrado!'],
    navMessages: ['📋 Cargando el perfil…','🎮 Obteniendo el equipo Pokémon…','✅ ¡Listo!'],
    navTitle: 'Cargando el perfil…',
    labelSrOnly: 'Buscar un nombre',
    placeholder: 'Tu nombre o el de un amigo…',
    ariaInput: 'Introduce un nombre',
    btnSearch: 'Encontrar mi entrenador ⚡',
    ariaResults: 'Resultados',
    ariaLoading: 'Cargando',
    ariaShare: 'Compartir',
    ariaClose: 'Cerrar',
    count0: (q) => `¡Ningún entrenador se llama "${q}" — es único en el mundo!`,
    count1: (q) => `¡Solo 1 entrenador legendario se llama "${q}"!`,
    countN: (n, q) => `${n} entrenadores se llaman "${q}"`,
    seeFullPage: 'Ver página completa →',
    shareBtn: '🎉 Compartir mi resultado',
    seeAllTrainers: (n) => `Ver los ${n} entrenadores →`,
    shareLbl0: '¡Nombre no encontrado en el mundo Pokémon!',
    shareLbl1: 'Solo 1 entrenador legendario lleva este nombre',
    shareLblN: (n, lbl) => `${n} entrenadores tienen este nombre · ${lbl}`,
    shareText0: (q) => `Mi nombre "${q}" no existe en ningún entrenador Pokémon — ¡es único! 🌟 pokenom.fr`,
    shareText1: (q) => `¡Mi nombre "${q}" solo pertenece a un entrenador legendario! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `Hay ${n} entrenadores Pokémon llamados "${q}" ${e} pokenom.fr`,
    copy: '📋 Copiar',
    copied: '✓ ¡Copiado!',
    shareNative: '🔗 Compartir',
    viewPage: 'Ver página →',
    rarityLabels: { unique:'Inexistente', legendaire:'Legendario', rare:'Raro', repandu:'Común', partout:'¡En todas partes!' },
  },
  ja: {
    searchMessages: ['🔍 名前を分析中…','📚 アーカイブを検索中…','⚡ トレーナーを特定中…','✅ トレーナーが見つかりました！'],
    navMessages: ['📋 プロフィール読み込み中…','🎮 ポケモンチームを取得中…','✅ 準備完了！'],
    navTitle: 'プロフィール読み込み中…',
    labelSrOnly: '名前を検索',
    placeholder: '自分や友達の名前…',
    ariaInput: '名前を入力',
    btnSearch: 'トレーナーを探す ⚡',
    ariaResults: '検索結果',
    ariaLoading: '読み込み中',
    ariaShare: 'シェア',
    ariaClose: '閉じる',
    count0: (q) => `「${q}」という名前のトレーナーはいません — 世界でも唯一！`,
    count1: (q) => `「${q}」という名前の伝説のトレーナーは1人だけ！`,
    countN: (n, q) => `「${q}」という名前のトレーナーが${n}人います`,
    seeFullPage: '詳細ページを見る →',
    shareBtn: '🎉 結果をシェア',
    seeAllTrainers: (n) => `${n}人のトレーナーを全員見る →`,
    shareLbl0: 'ポケモンの世界にない名前！',
    shareLbl1: 'この名前を持つ伝説のトレーナーは1人だけ',
    shareLblN: (n, lbl) => `この名前を持つトレーナーが${n}人 · ${lbl}`,
    shareText0: (q) => `私の名前「${q}」はポケモントレーナーに存在しない — ユニーク！🌟 pokenom.fr`,
    shareText1: (q) => `私の名前「${q}」は伝説のトレーナー1人だけのもの！🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `「${q}」という名前のポケモントレーナーが${n}人います ${e} pokenom.fr`,
    copy: '📋 コピー',
    copied: '✓ コピーしました！',
    shareNative: '🔗 シェア',
    viewPage: 'ページを見る →',
    rarityLabels: { unique:'存在しない', legendaire:'伝説', rare:'レア', repandu:'一般的', partout:'どこでも！' },
  },
  it: {
    searchMessages: ['🔍 Analisi del nome…','📚 Consultazione degli archivi…','⚡ Identificazione dell\'allenatore…','✅ Allenatore trovato!'],
    navMessages: ['📋 Caricamento del profilo…','🎮 Recupero del team Pokémon…','✅ Pronto!'],
    navTitle: 'Caricamento del profilo…',
    labelSrOnly: 'Cerca un nome',
    placeholder: 'Il tuo nome o quello di un amico…',
    ariaInput: 'Inserisci un nome',
    btnSearch: 'Trova il mio allenatore ⚡',
    ariaResults: 'Risultati',
    ariaLoading: 'Caricamento',
    ariaShare: 'Condividi',
    ariaClose: 'Chiudi',
    count0: (q) => `Nessun allenatore si chiama "${q}" — è unico al mondo!`,
    count1: (q) => `Solo 1 allenatore leggendario si chiama "${q}"!`,
    countN: (n, q) => `${n} allenatori si chiamano "${q}"`,
    seeFullPage: 'Vedi la pagina completa →',
    shareBtn: '🎉 Condividi il risultato',
    seeAllTrainers: (n) => `Vedi tutti i ${n} allenatori →`,
    shareLbl0: 'Nome non trovato nel mondo Pokémon!',
    shareLbl1: 'Solo 1 allenatore leggendario porta questo nome',
    shareLblN: (n, lbl) => `${n} allenatori hanno questo nome · ${lbl}`,
    shareText0: (q) => `Il mio nome "${q}" non esiste in nessun allenatore Pokémon — è unico! 🌟 pokenom.fr`,
    shareText1: (q) => `Il mio nome "${q}" appartiene a un solo allenatore leggendario! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `Ci sono ${n} allenatori Pokémon chiamati "${q}" ${e} pokenom.fr`,
    copy: '📋 Copia',
    copied: '✓ Copiato!',
    shareNative: '🔗 Condividi',
    viewPage: 'Vedi la pagina →',
    rarityLabels: { unique:'Introvabile', legendaire:'Leggendario', rare:'Raro', repandu:'Comune', partout:'Ovunque!' },
  },
  ko: {
    searchMessages: ['🔍 이름 분석 중…','📚 아카이브 조회 중…','⚡ 트레이너 식별 중…','✅ 트레이너 발견!'],
    navMessages: ['📋 프로필 로딩 중…','🎮 포켓몬 팀 불러오는 중…','✅ 준비 완료!'],
    navTitle: '프로필 로딩 중…',
    labelSrOnly: '이름 검색',
    placeholder: '나 또는 친구의 이름…',
    ariaInput: '이름 입력',
    btnSearch: '내 트레이너 찾기 ⚡',
    ariaResults: '검색 결과',
    ariaLoading: '로딩 중',
    ariaShare: '공유',
    ariaClose: '닫기',
    count0: (q) => `"${q}"라는 이름의 트레이너가 없습니다 — 세상에서 유일해요!`,
    count1: (q) => `"${q}"라는 이름의 전설적인 트레이너가 딱 1명 있어요!`,
    countN: (n, q) => `"${q}"라는 이름의 트레이너가 ${n}명 있어요`,
    seeFullPage: '전체 페이지 보기 →',
    shareBtn: '🎉 결과 공유하기',
    seeAllTrainers: (n) => `${n}명 트레이너 모두 보기 →`,
    shareLbl0: '포켓몬 세계에서 찾을 수 없는 이름!',
    shareLbl1: '이 이름을 가진 전설적인 트레이너 단 1명',
    shareLblN: (n, lbl) => `이 이름을 가진 트레이너 ${n}명 · ${lbl}`,
    shareText0: (q) => `내 이름 "${q}"은 어떤 포켓몬 트레이너에도 없어요 — 독보적! 🌟 pokenom.fr`,
    shareText1: (q) => `내 이름 "${q}"은 단 한 명의 전설적인 트레이너의 것! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `"${q}"라는 이름의 포켓몬 트레이너가 ${n}명 있어요 ${e} pokenom.fr`,
    copy: '📋 복사',
    copied: '✓ 복사됨!',
    shareNative: '🔗 공유',
    viewPage: '페이지 보기 →',
    rarityLabels: { unique:'존재 안 함', legendaire:'전설', rare:'희귀', repandu:'일반', partout:'어디든!' },
  },
  'zh-Hans': {
    searchMessages: ['🔍 分析名字中…','📚 查阅档案中…','⚡ 识别训练师中…','✅ 找到训练师！'],
    navMessages: ['📋 加载档案中…','🎮 获取宝可梦队伍中…','✅ 准备就绪！'],
    navTitle: '加载档案中…',
    labelSrOnly: '搜索名字',
    placeholder: '你或朋友的名字…',
    ariaInput: '输入名字',
    btnSearch: '找我的训练师 ⚡',
    ariaResults: '结果',
    ariaLoading: '加载中',
    ariaShare: '分享',
    ariaClose: '关闭',
    count0: (q) => `没有训练师叫"${q}" — 这个名字举世独一无二！`,
    count1: (q) => `只有1位传奇训练师叫"${q}"！`,
    countN: (n, q) => `有${n}位训练师叫"${q}"`,
    seeFullPage: '查看完整页面 →',
    shareBtn: '🎉 分享我的结果',
    seeAllTrainers: (n) => `查看全部${n}位训练师 →`,
    shareLbl0: '在宝可梦世界中找不到这个名字！',
    shareLbl1: '只有1位传奇训练师拥有这个名字',
    shareLblN: (n, lbl) => `${n}位训练师有这个名字 · ${lbl}`,
    shareText0: (q) => `我的名字"${q}"在所有宝可梦训练师中不存在 — 独一无二！🌟 pokenom.fr`,
    shareText1: (q) => `我的名字"${q}"只属于一位传奇训练师！🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `有${n}位宝可梦训练师叫"${q}" ${e} pokenom.fr`,
    copy: '📋 复制',
    copied: '✓ 已复制！',
    shareNative: '🔗 分享',
    viewPage: '查看页面 →',
    rarityLabels: { unique:'不存在', legendaire:'传奇', rare:'稀有', repandu:'普通', partout:'随处可见！' },
  },
  'zh-Hant': {
    searchMessages: ['🔍 分析名字中…','📚 查閱檔案中…','⚡ 識別訓練師中…','✅ 找到訓練師！'],
    navMessages: ['📋 載入檔案中…','🎮 獲取寶可夢隊伍中…','✅ 準備就緒！'],
    navTitle: '載入檔案中…',
    labelSrOnly: '搜尋名字',
    placeholder: '你或朋友的名字…',
    ariaInput: '輸入名字',
    btnSearch: '找我的訓練師 ⚡',
    ariaResults: '結果',
    ariaLoading: '載入中',
    ariaShare: '分享',
    ariaClose: '關閉',
    count0: (q) => `沒有訓練師叫「${q}」— 這個名字舉世獨一無二！`,
    count1: (q) => `只有1位傳奇訓練師叫「${q}」！`,
    countN: (n, q) => `有${n}位訓練師叫「${q}」`,
    seeFullPage: '查看完整頁面 →',
    shareBtn: '🎉 分享我的結果',
    seeAllTrainers: (n) => `查看全部${n}位訓練師 →`,
    shareLbl0: '在寶可夢世界中找不到這個名字！',
    shareLbl1: '只有1位傳奇訓練師擁有這個名字',
    shareLblN: (n, lbl) => `${n}位訓練師有這個名字 · ${lbl}`,
    shareText0: (q) => `我的名字「${q}」在所有寶可夢訓練師中不存在 — 獨一無二！🌟 pokenom.fr`,
    shareText1: (q) => `我的名字「${q}」只屬於一位傳奇訓練師！🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `有${n}位寶可夢訓練師叫「${q}」${e} pokenom.fr`,
    copy: '📋 複製',
    copied: '✓ 已複製！',
    shareNative: '🔗 分享',
    viewPage: '查看頁面 →',
    rarityLabels: { unique:'不存在', legendaire:'傳奇', rare:'稀有', repandu:'普通', partout:'隨處可見！' },
  },
  'pt-BR': {
    searchMessages: ['🔍 Analisando o nome…','📚 Consultando os arquivos…','⚡ Identificando o treinador…','✅ Treinador encontrado!'],
    navMessages: ['📋 Carregando o perfil…','🎮 Obtendo o time Pokémon…','✅ Pronto!'],
    navTitle: 'Carregando o perfil…',
    labelSrOnly: 'Pesquisar um nome',
    placeholder: 'Seu nome ou de um amigo…',
    ariaInput: 'Digite um nome',
    btnSearch: 'Encontrar meu treinador ⚡',
    ariaResults: 'Resultados',
    ariaLoading: 'Carregando',
    ariaShare: 'Compartilhar',
    ariaClose: 'Fechar',
    count0: (q) => `Nenhum treinador se chama "${q}" — é único no mundo!`,
    count1: (q) => `Apenas 1 treinador lendário se chama "${q}"!`,
    countN: (n, q) => `${n} treinadores se chamam "${q}"`,
    seeFullPage: 'Ver página completa →',
    shareBtn: '🎉 Compartilhar resultado',
    seeAllTrainers: (n) => `Ver todos os ${n} treinadores →`,
    shareLbl0: 'Nome não encontrado no mundo Pokémon!',
    shareLbl1: 'Apenas 1 treinador lendário tem esse nome',
    shareLblN: (n, lbl) => `${n} treinadores têm esse nome · ${lbl}`,
    shareText0: (q) => `Meu nome "${q}" não existe em nenhum treinador Pokémon — é único! 🌟 pokenom.fr`,
    shareText1: (q) => `Meu nome "${q}" pertence a apenas um treinador lendário! 🏆 pokenom.fr`,
    shareTextN: (n, q, e) => `Há ${n} treinadores Pokémon chamados "${q}" ${e} pokenom.fr`,
    copy: '📋 Copiar',
    copied: '✓ Copiado!',
    shareNative: '🔗 Compartilhar',
    viewPage: 'Ver página →',
    rarityLabels: { unique:'Inexistente', legendaire:'Lendário', rare:'Raro', repandu:'Comum', partout:'Em todo lugar!' },
  },
};

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
  title, messages, duration, slot, onDone, navTarget, ariaLabel,
}: {
  title: string; messages: string[]; duration: number;
  slot: string; onDone: () => void; navTarget?: string; ariaLabel?: string;
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
    <div class="modal-backdrop" role="dialog" aria-modal="true" aria-label={ariaLabel ?? 'Loading'}>
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
  query, count, rarityEmoji, rarityLabel, rarityKey, onClose, i18n,
}: {
  query: string; count: number; rarityEmoji: string;
  rarityLabel: string; rarityKey: string; onClose: () => void;
  i18n: typeof SEARCH_I18N[string];
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => { ensureModalCss(); }, []);

  const shareText = count === 0
    ? i18n.shareText0(query)
    : count === 1
    ? i18n.shareText1(query)
    : i18n.shareTextN(count, query, rarityEmoji);

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
    <div class="modal-backdrop" role="dialog" aria-modal="true" aria-label={i18n.ariaShare} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div class="share-card">
        <button class="share-close" onClick={onClose} aria-label={i18n.ariaClose}>✕</button>

        <div class="share-rarity-big"><img src={`/assets/rarity/${rarityKey}.svg`} alt="" width="48" height="48" /></div>
        <p class="share-name">"{query}"</p>
        <p class="share-label">
          {count === 0
            ? i18n.shareLbl0
            : count === 1
            ? i18n.shareLbl1
            : i18n.shareLblN(count, rarityLabel)
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
            {copied ? i18n.copied : i18n.copy}
          </button>
          {typeof navigator !== 'undefined' && 'share' in navigator && (
            <button class="share-btn" onClick={handleNative}>
              {i18n.shareNative}
            </button>
          )}
          {count > 0 && (
            <a
              href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`}
              class="share-btn"
            >
              {i18n.viewPage}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Composant principal ────────────────────────────────────────────────────
// ── Helpers de traduction pour les résultats ─────────────────────────────
function translateClass(frClass: string, lang: string): string {
  if (lang === 'fr') return frClass;
  return TC[frClass]?.[lang] ?? frClass;
}
function translateGame(frGame: string, lang: string): string {
  if (lang === 'fr') return frGame.replace('Pokémon ', '');
  const games = (typeof window !== 'undefined' ? (window as any).__pokenom_T?.games : null) as Record<string, Record<string, string>> | null;
  return games?.[frGame]?.[lang]?.replace('Pokémon ', '') ?? frGame.replace('Pokémon ', '');
}
function translateTeam(team: string[], lang: string, pkmNames: Record<string, Record<string, string>>): string {
  if (lang === 'fr') return team.slice(0, 3).join(', ') + (team.length > 3 ? '…' : '');
  const translated = team.slice(0, 3).map(pkm => pkmNames[pkm]?.[lang] ?? pkm);
  return translated.join(', ') + (team.length > 3 ? '…' : '');
}

export default function Search({ trainers, pkmNames = {} }: SearchProps) {
  const i18n = SEARCH_I18N[getLang()] ?? SEARCH_I18N['fr'];
  const lang  = getLang();
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
  const rarityLabel= i18n.rarityLabels[rarityKey] ?? rarityKey;

  return (
    <div class="search-island">

      {/* ── Modale recherche (2.6s) ── */}
      {showSearchModal && (
        <ProgressModal
          title={`"${pendingQuery}"`}
          messages={i18n.searchMessages}
          duration={MODAL_DURATION}
          slot="2896100570"
          onDone={handleSearchDone}
          ariaLabel={i18n.ariaLoading}
        />
      )}

      {/* ── Modale navigation (1.5s) ── */}
      {navTarget && (
        <ProgressModal
          title={i18n.navTitle}
          messages={i18n.navMessages}
          duration={NAV_DURATION}
          slot="2896100570"
          onDone={handleNavDone}
          navTarget={navTarget}
          ariaLabel={i18n.ariaLoading}
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
          i18n={i18n}
        />
      )}

      <form onSubmit={handleSubmit} class="search-form" role="search">
        <div class="search-input-wrap" style="position:relative">
          <label for="search-q" class="sr-only">{i18n.labelSrOnly}</label>
          <input
            id="search-q"
            ref={inputRef}
            type="search"
            value={query}
            onInput={handleInput}
            onKeyDown={handleKeyDown}
            onFocus={() => { if (suggestions.length > 0) setShowSugg(true); }}
            onBlur={() => { blurTimer.current = setTimeout(() => setShowSugg(false), 150); }}
            placeholder={i18n.placeholder}
            autocomplete="off"
            spellcheck={false}
            maxLength={40}
            class="search-input"
            aria-label={i18n.ariaInput}
            aria-autocomplete="list"
            aria-expanded={showSugg}
            aria-controls="autocomplete-list"
          />
          <button type="submit" class="search-btn" aria-label={i18n.btnSearch}>
            {i18n.btnSearch}
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
        <div class="search-results" role="region" aria-live="polite" aria-label={i18n.ariaResults}>
          <div class="results-header">
            <span class={`rarity rarity--${rarityKey}`}>
              <img src={`/assets/rarity/${rarityKey}.svg`} alt="" width="14" height="14" style="vertical-align:middle;margin-right:4px;" /> {rarityLabel}
            </span>
            <p class="results-count">
              {count === 0
                ? i18n.count0(query)
                : count === 1
                ? i18n.count1(query)
                : i18n.countN(count, query)
              }
            </p>
            {count > 0 && (
              <a href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`} class="see-page-link">
                {i18n.seeFullPage}
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
              {i18n.shareBtn}
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
                      <span class="result-class">{translateClass(t.class, lang)}</span>
                      <strong class="result-name">{t.name}</strong>
                    </div>
                    <div class="result-item__right">
                      <span class="result-game">{translateGame(t.game, lang)}</span>
                      {t.team && t.team.length > 0 && (
                        <span class="result-team">{translateTeam(t.team, lang, pkmNames)}</span>
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
                      <span class="result-class">{translateClass(t.class, lang)}</span>
                      <strong class="result-name">{t.name}</strong>
                    </div>
                    <div class="result-item__right">
                      <span class="result-game">{translateGame(t.game, lang)}</span>
                      {t.team && t.team.length > 0 && (
                        <span class="result-team">{translateTeam(t.team, lang, pkmNames)}</span>
                      )}
                    </div>
                    <span class="result-arrow">→</span>
                  </a>
                </li>
              ))}

              {count > 8 && (
                <li>
                  <a href={`/prenom/${normalize(query).replace(/\s+/g, '-')}`} class="see-all-link">
                    {i18n.seeAllTrainers(count)}
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
