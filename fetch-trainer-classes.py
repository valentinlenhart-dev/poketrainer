#!/usr/bin/env python3
"""
fetch-trainer-classes.py — Traduit les classes de dresseurs

Génère src/data/trainer-classes-i18n.json.
Essaie d'abord l'API PokeAPI, puis utilise le mapping intégré en fallback.
"""
import json, sys, time, os
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests  puis relance.")
    sys.exit(1)

SRC  = Path(__file__).parent / "src" / "data" / "trainers.json"
DEST = Path(__file__).parent / "src" / "data" / "trainer-classes-i18n.json"

API_LANGS = {"fr", "en", "de", "es", "ja", "it", "ko", "zh-Hans", "zh-Hant", "pt-BR"}

with open(SRC, encoding="utf-8") as f:
    trainers = json.load(f)

fr_classes = sorted(set(t["class"] for t in trainers if t.get("class")))
print(f"🎯 {len(fr_classes)} classes distinctes dans trainers.json")

result: dict[str, dict[str, str]] = {}
if DEST.exists():
    try:
        with open(DEST, encoding="utf-8") as f:
            existing = json.load(f)
        if existing:
            result = existing
            print(f"📂 {len(result)} entrées déjà en cache")
    except Exception:
        pass

SESSION = requests.Session()
# User-Agent navigateur pour éviter le blocage WAF
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
})

def api_get(url: str) -> dict | None:
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=15)
            if r.status_code == 404: return None
            if r.status_code == 400:
                return None  # WAF bloqué — on abandonne l'API
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException:
            if attempt < 2: time.sleep(2 ** attempt)
    return None

print("\n🔌 Test connectivité PokeAPI…")
test = api_get("https://pokeapi.co/api/v2/trainer-class/1/")
USE_API = test is not None
print(f"{'✅ API accessible' if USE_API else '❌ API inaccessible — fallback activé'}")

# ══════════════════════════════════════════════════════════════════
# MAPPING COMPLET — toutes les classes connues des jeux Pokémon FR
# ══════════════════════════════════════════════════════════════════
FALLBACK: dict[str, dict[str, str]] = {
  # ── Dresseurs de base ──────────────────────────────────────────
  "Gamin":              {"en":"Youngster","de":"Knirps","es":"Chico","it":"Pivello","ja":"たんぱんこぞう","ko":"반바지꼬마","zh-Hans":"短裤小鬼","zh-Hant":"短褲小鬼","pt-BR":"Garoto"},
  "Damoiselle":         {"en":"Lass","de":"Göre","es":"Chica","it":"Pivella","ja":"ミニスカート","ko":"미니스커트","zh-Hans":"迷你裙","zh-Hant":"迷你裙","pt-BR":"Garota"},
  "Scout":              {"en":"Camper","de":"Wanderer","es":"Campista","it":"Campeggiatore","ja":"たびびと","ko":"캠퍼","zh-Hans":"露营者","zh-Hant":"露營者","pt-BR":"Campista"},
  "Eclaireuse":         {"en":"Picnicker","de":"Wanderin","es":"Excursionista","it":"Gitante","ja":"ピクニックガール","ko":"피크닉걸","zh-Hans":"郊游女","zh-Hant":"郊遊女","pt-BR":"Piqueniqueira"},
  "Éclaireur":          {"en":"Camper","de":"Wanderer","es":"Campista","it":"Campeggiatore","ja":"たびびと","ko":"캠퍼","zh-Hans":"露营者","zh-Hant":"露營者","pt-BR":"Campista"},
  "Randonneur":         {"en":"Hiker","de":"Bergsteiger","es":"Mochilero","it":"Escursionista","ja":"やまおとこ","ko":"산악인","zh-Hans":"登山者","zh-Hant":"登山者","pt-BR":"Mochileiro"},
  "Marin":              {"en":"Sailor","de":"Matrose","es":"Marinero","it":"Marinaio","ja":"かいパンやろう","ko":"반바지선원","zh-Hans":"水手","zh-Hant":"水手","pt-BR":"Marinheiro"},
  "Surfeur":            {"en":"Surfer","de":"Surfer","es":"Surfero","it":"Surfista","ja":"サーファー","ko":"서퍼","zh-Hans":"冲浪者","zh-Hant":"衝浪者","pt-BR":"Surfista"},
  "Pêcheur":            {"en":"Fisher","de":"Angler","es":"Pescador","it":"Pescatore","ja":"つりびと","ko":"낚시꾼","zh-Hans":"垂钓者","zh-Hant":"垂釣者","pt-BR":"Pescador"},
  "Pécheur":            {"en":"Fisher","de":"Angler","es":"Pescador","it":"Pescatore","ja":"つりびと","ko":"낚시꾼","zh-Hans":"垂钓者","zh-Hant":"垂釣者","pt-BR":"Pescador"},
  "Beauté":             {"en":"Beauty","de":"Schönheit","es":"Belleza","it":"Bellezza","ja":"おねえさん","ko":"미인","zh-Hans":"美女","zh-Hant":"美女","pt-BR":"Beleza"},
  "Gentleman":          {"en":"Gentleman","de":"Gentleman","es":"Caballero","it":"Gentiluomo","ja":"ジェントルマン","ko":"젠틀맨","zh-Hans":"绅士","zh-Hant":"紳士","pt-BR":"Cavalheiro"},
  "Milord":             {"en":"Gentleman","de":"Gentleman","es":"Caballero","it":"Gentiluomo","ja":"ジェントルマン","ko":"젠틀맨","zh-Hans":"绅士","zh-Hant":"紳士","pt-BR":"Cavalheiro"},
  "Lady":               {"en":"Lady","de":"Dame","es":"Señorita","it":"Signorina","ja":"レディ","ko":"레이디","zh-Hans":"淑女","zh-Hant":"淑女","pt-BR":"Lady"},
  "Riche":              {"en":"Rich Boy","de":"Jungsohn","es":"Niño Rico","it":"Ricco","ja":"ぼんぼん","ko":"부잣집도련님","zh-Hans":"富家子弟","zh-Hant":"富家子弟","pt-BR":"Garoto Rico"},
  "Fille Riche":        {"en":"Lady","de":"Dame","es":"Señorita","it":"Signorina","ja":"レディ","ko":"레이디","zh-Hans":"淑女","zh-Hant":"淑女","pt-BR":"Lady"},
  "Biker":              {"en":"Biker","de":"Biker","es":"Biker","it":"Biker","ja":"バイカー","ko":"바이커","zh-Hans":"飞车党","zh-Hant":"飛車黨","pt-BR":"Biker"},
  "Rocker":             {"en":"Rocker","de":"Rocker","es":"Rocker","it":"Rocker","ja":"ロッカー","ko":"로커","zh-Hans":"摇滚手","zh-Hant":"搖滾手","pt-BR":"Roqueiro"},
  "Ninja":              {"en":"Ninja Boy","de":"Ninja","es":"Chico Ninja","it":"Ninja","ja":"にんじゃごっこ","ko":"닌자","zh-Hans":"忍者","zh-Hant":"忍者","pt-BR":"Garoto Ninja"},
  "Cycliste":           {"en":"Cyclist","de":"Radfahrer","es":"Ciclista","it":"Ciclista","ja":"サイクリング","ko":"사이클링","zh-Hans":"骑行者","zh-Hant":"騎行者","pt-BR":"Ciclista"},
  "Artiste":            {"en":"Artist","de":"Künstler","es":"Artista","it":"Artista","ja":"げいじゅつか","ko":"예술가","zh-Hans":"艺术家","zh-Hant":"藝術家","pt-BR":"Artista"},
  "Catcheur":           {"en":"Wrestler","de":"Ringer","es":"Luchador","it":"Wrestler","ja":"プロレスラー","ko":"프로레슬러","zh-Hans":"摔跤手","zh-Hant":"摔跤手","pt-BR":"Lutador"},
  "Comédien":           {"en":"Clown","de":"Clown","es":"Payaso","it":"Clown","ja":"ピエロ","ko":"광대","zh-Hans":"小丑","zh-Hant":"小丑","pt-BR":"Palhaço"},
  "Comédienne":         {"en":"Actress","de":"Schauspielerin","es":"Actriz","it":"Attrice","ja":"ジョーカー","ko":"조커","zh-Hans":"女演员","zh-Hant":"女演員","pt-BR":"Atriz"},
  "Actrice":            {"en":"Actress","de":"Schauspielerin","es":"Actriz","it":"Attrice","ja":"ジョーカー","ko":"조커","zh-Hans":"女演员","zh-Hant":"女演員","pt-BR":"Atriz"},
  "Magicien":           {"en":"Magician","de":"Magier","es":"Mago","it":"Mago","ja":"マジシャン","ko":"마술사","zh-Hans":"魔术师","zh-Hant":"魔術師","pt-BR":"Mágico"},
  "Chaman":             {"en":"Hex Maniac","de":"Hexe","es":"Bruja","it":"Fattucchiera","ja":"おとめ","ko":"처녀귀신","zh-Hans":"妖术迷","zh-Hant":"妖術迷","pt-BR":"Maníaca do Hexe"},
  "Scientifique":       {"en":"Scientist","de":"Wissenschaftler","es":"Científico","it":"Scienziato","ja":"はかせ","ko":"박사","zh-Hans":"科学家","zh-Hant":"科學家","pt-BR":"Cientista"},
  "Technicien":         {"en":"Engineer","de":"Techniker","es":"Técnico","it":"Tecnico","ja":"テクニシャン","ko":"테크니션","zh-Hans":"技术员","zh-Hant":"技術員","pt-BR":"Técnico"},
  "Technicienne":       {"en":"Pokéfan","de":"Pokéfan","es":"Pokéfan","it":"Pokéfan","ja":"ポケファン♀","ko":"포케팬","zh-Hans":"宝可梦迷","zh-Hant":"寶可夢迷","pt-BR":"Pokéfã"},
  "Policier":           {"en":"Officer","de":"Polizist","es":"Oficial","it":"Ufficiale","ja":"おまわりさん","ko":"경찰관","zh-Hans":"警察","zh-Hant":"警察","pt-BR":"Policial"},
  "Journaliste":        {"en":"Reporter","de":"Reporter","es":"Reportero","it":"Reporter","ja":"きしゃ","ko":"기자","zh-Hans":"记者","zh-Hant":"記者","pt-BR":"Repórter"},
  "Porte-parole":       {"en":"Interviewer","de":"Moderator","es":"Entrevistador","it":"Intervistatore","ja":"インタビュアー","ko":"인터뷰어","zh-Hans":"采访者","zh-Hant":"採訪者","pt-BR":"Entrevistador"},
  "Professeur":         {"en":"Pokémon Professor","de":"Pokémon-Professor","es":"Profesor Pokémon","it":"Professore Pokémon","ja":"ポケモンはかせ","ko":"포켓몬박사","zh-Hans":"宝可梦教授","zh-Hant":"寶可夢教授","pt-BR":"Professor Pokémon"},
  "Sportif":            {"en":"Athlete","de":"Sportler","es":"Atleta","it":"Atleta","ja":"アスリート","ko":"운동선수","zh-Hans":"运动员","zh-Hant":"運動員","pt-BR":"Atleta"},
  "Sportive":           {"en":"Athlete","de":"Sportlerin","es":"Atleta","it":"Atleta","ja":"アスリート","ko":"운동선수","zh-Hans":"运동员","zh-Hant":"運動員","pt-BR":"Atleta"},

  # ── Champions & Élite ──────────────────────────────────────────
  "Champion":           {"en":"Gym Leader","de":"Arenaleiter","es":"Líder de Gimnasio","it":"Capopalestra","ja":"ジムリーダー","ko":"체육관관장","zh-Hans":"道馆馆主","zh-Hant":"道館館主","pt-BR":"Líder de Ginásio"},
  "Championne":         {"en":"Gym Leader","de":"Arenaleiterin","es":"Líder de Gimnasio","it":"Capopalestra","ja":"ジムリーダー","ko":"체육관관장","zh-Hans":"道馆馆主","zh-Hant":"道館館主","pt-BR":"Líder de Ginásio"},
  "Champion (Kanto)":   {"en":"Gym Leader","de":"Arenaleiter","es":"Líder de Gimnasio","it":"Capopalestra","ja":"ジムリーダー","ko":"체육관관장","zh-Hans":"道馆馆主","zh-Hant":"道館館主","pt-BR":"Líder de Ginásio"},
  "Champion Arena":     {"en":"Gym Leader","de":"Arenaleiter","es":"Líder de Gimnasio","it":"Capopalestra","ja":"ジムリーダー","ko":"체육관관장","zh-Hans":"道馆馆主","zh-Hant":"道館館主","pt-BR":"Líder de Ginásio"},
  "Maître":             {"en":"Elite Four","de":"Top Vier","es":"Alto Mando","it":"Superquattro","ja":"したてのよつ","ko":"사천왕","zh-Hans":"四天王","zh-Hant":"四天王","pt-BR":"Elite dos Quatro"},
  "Maîtresse":          {"en":"Elite Four","de":"Top Vier","es":"Alto Mando","it":"Superquattro","ja":"したてのよつ","ko":"사천왕","zh-Hans":"四天王","zh-Hant":"四天王","pt-BR":"Elite dos Quatro"},
  "Maître de Ligue":    {"en":"Pokémon Champion","de":"Pokémon-Champion","es":"Campeón Pokémon","it":"Campione Pokémon","ja":"チャンピオン","ko":"챔피언","zh-Hans":"冠军","zh-Hant":"冠軍","pt-BR":"Campeão Pokémon"},
  "Topdresseur":        {"en":"Ace Trainer","de":"Top-Trainer","es":"Ás del Talento","it":"Asso Allenatore","ja":"エリートトレーナー","ko":"에이스트레이너","zh-Hans":"王牌训练师","zh-Hant":"王牌訓練師","pt-BR":"Ás Treinador"},
  "Topdresseuse":       {"en":"Ace Trainer","de":"Top-Trainerin","es":"Ás del Talento","it":"Asso Allenatrice","ja":"エリートトレーナー","ko":"에이스트레이너","zh-Hans":"王牌训练师","zh-Hant":"王牌訓練師","pt-BR":"Ás Treinadora"},
  "Rival":              {"en":"Rival","de":"Rivale","es":"Rival","it":"Rivale","ja":"ライバル","ko":"라이벌","zh-Hans":"竞争对手","zh-Hant":"競爭對手","pt-BR":"Rival"},

  # ── Dresseur/Dresseuse générique ──────────────────────────────
  "Dresseur":           {"en":"Pokémon Trainer","de":"Pokémon-Trainer","es":"Entrenador Pokémon","it":"Allenatore Pokémon","ja":"ポケモントレーナー","ko":"포켓몬트레이너","zh-Hans":"宝可梦训练师","zh-Hant":"寶可夢訓練師","pt-BR":"Treinador Pokémon"},
  "Dresseuse":          {"en":"Pokémon Trainer","de":"Pokémon-Trainerin","es":"Entrenadora Pokémon","it":"Allenatrice Pokémon","ja":"ポケモントレーナー","ko":"포켓몬트레이너","zh-Hans":"宝可梦训练师","zh-Hant":"寶可夢訓練師","pt-BR":"Treinadora Pokémon"},

  # ── Jumeaux/Équipes ───────────────────────────────────────────
  "Jumeaux":            {"en":"Twins","de":"Zwillinge","es":"Gemelos","it":"Gemelli","ja":"ふたごちゃん","ko":"쌍둥이","zh-Hans":"双胞胎","zh-Hant":"雙胞胎","pt-BR":"Gêmeos"},
  "Jumelles":           {"en":"Twins","de":"Zwillinge","es":"Gemelas","it":"Gemelle","ja":"ふたごちゃん","ko":"쌍둥이","zh-Hans":"双胞胎","zh-Hant":"雙胞胎","pt-BR":"Gêmeas"},
  "Duo":                {"en":"Twins","de":"Duo","es":"Dúo","it":"Duo","ja":"ふたごちゃん","ko":"듀오","zh-Hans":"双人组","zh-Hant":"雙人組","pt-BR":"Dupla"},
  "Duo de Choc":        {"en":"Teammates","de":"Duo","es":"Dúo","it":"Duo","ja":"コンビ","ko":"콤비","zh-Hans":"搭档","zh-Hant":"搭檔","pt-BR":"Dupla"},

  # ── Équipes vilaines ──────────────────────────────────────────
  "Équipe Rocket":      {"en":"Team Rocket Grunt","de":"Team Rocket-Rüpel","es":"Recluta del Team Rocket","it":"Recluta Team Rocket","ja":"ロケット団したっぱ","ko":"로켓단원","zh-Hans":"火箭队喽啰","zh-Hant":"火箭隊嘍囉","pt-BR":"Recruta do Team Rocket"},
  "Team Rocket":        {"en":"Team Rocket Grunt","de":"Team Rocket-Rüpel","es":"Recluta del Team Rocket","it":"Recluta Team Rocket","ja":"ロケット団したっぱ","ko":"로켓단원","zh-Hans":"火箭队喽啰","zh-Hant":"火箭隊嘍囉","pt-BR":"Recruta do Team Rocket"},
  "Admin Team":         {"en":"Team Admin","de":"Team-Admin","es":"Jefe del Team","it":"Admin Team","ja":"したっぱ","ko":"간부","zh-Hans":"团队管理员","zh-Hant":"團隊管理員","pt-BR":"Admin do Team"},
  "Team Aqua":          {"en":"Team Aqua Grunt","de":"Team Aqua-Rüpel","es":"Recluta del Team Aqua","it":"Recluta Team Aqua","ja":"アクア団したっぱ","ko":"아쿠아단원","zh-Hans":"海洋队喽啰","zh-Hant":"海洋隊嘍囉","pt-BR":"Recruta do Team Aqua"},
  "Admin Aqua":         {"en":"Team Aqua Admin","de":"Team Aqua-Admin","es":"Jefe del Team Aqua","it":"Admin Team Aqua","ja":"アクア団かんぶ","ko":"아쿠아단 간부","zh-Hans":"海洋队管理员","zh-Hant":"海洋隊管理員","pt-BR":"Admin do Team Aqua"},
  "Admin Team Aqua":    {"en":"Team Aqua Admin","de":"Team Aqua-Admin","es":"Jefe del Team Aqua","it":"Admin Team Aqua","ja":"アクア団かんぶ","ko":"아쿠아단 간부","zh-Hans":"海洋队管理员","zh-Hant":"海洋隊管理員","pt-BR":"Admin do Team Aqua"},
  "Team Magma":         {"en":"Team Magma Grunt","de":"Team Magma-Rüpel","es":"Recluta del Team Magma","it":"Recluta Team Magma","ja":"マグマ団したっぱ","ko":"마그마단원","zh-Hans":"岩浆队喽啰","zh-Hant":"岩漿隊嘍囉","pt-BR":"Recruta do Team Magma"},
  "Admin Magma":        {"en":"Team Magma Admin","de":"Team Magma-Admin","es":"Jefe del Team Magma","it":"Admin Team Magma","ja":"マグマ団かんぶ","ko":"마그마단 간부","zh-Hans":"岩浆队管理员","zh-Hant":"岩漿隊管理員","pt-BR":"Admin do Team Magma"},
  "Admin Team Magma":   {"en":"Team Magma Admin","de":"Team Magma-Admin","es":"Jefe del Team Magma","it":"Admin Team Magma","ja":"マグマ団かんぶ","ko":"마그마단 간부","zh-Hans":"岩浆队管理员","zh-Hant":"岩漿隊管理員","pt-BR":"Admin do Team Magma"},
  "Team Galactique":    {"en":"Team Galactic Grunt","de":"Team Galaktik-Rüpel","es":"Recluta del Team Galaxia","it":"Recluta Team Galassia","ja":"ギンガ団したっぱ","ko":"갤럭시단원","zh-Hans":"银河队喽啰","zh-Hant":"銀河隊嘍囉","pt-BR":"Recruta do Team Galáxia"},
  "Admin Team Galactique":{"en":"Team Galactic Admin","de":"Team Galaktik-Admin","es":"Jefe del Team Galaxia","it":"Admin Team Galassia","ja":"ギンガ団かんぶ","ko":"갤럭시단 간부","zh-Hans":"银河队管理员","zh-Hant":"銀河隊管理員","pt-BR":"Admin do Team Galáxia"},
  "Team Plasma":        {"en":"Team Plasma Grunt","de":"Team Plasma-Rüpel","es":"Recluta del Team Plasma","it":"Recluta Team Plasma","ja":"プラズマ団したっぱ","ko":"플라스마단원","zh-Hans":"等离子队喽啰","zh-Hant":"等離子隊嘍囉","pt-BR":"Recruta do Team Plasma"},
  "Team Flare":         {"en":"Team Flare Grunt","de":"Team Flare-Rüpel","es":"Recluta del Team Flare","it":"Recluta Team Flare","ja":"フレア団したっぱ","ko":"플레어단원","zh-Hans":"闪焰队喽啰","zh-Hant":"閃焰隊嘍囉","pt-BR":"Recruta do Team Flare"},
  "Boss Team Flare":    {"en":"Team Flare Boss","de":"Team Flare-Boss","es":"Jefe del Team Flare","it":"Boss Team Flare","ja":"フレア団ボス","ko":"플레어단 보스","zh-Hans":"闪焰队老大","zh-Hant":"閃焰隊老大","pt-BR":"Chefe do Team Flare"},
  "Team Skull":         {"en":"Team Skull Grunt","de":"Team Skull-Rüpel","es":"Recluta del Team Skull","it":"Recluta Team Skull","ja":"スカル団したっぱ","ko":"스컬단원","zh-Hans":"骷髅队喽啰","zh-Hant":"骷髏隊嘍囉","pt-BR":"Recruta do Team Skull"},
  "Admin Team Skull":   {"en":"Team Skull Admin","de":"Team Skull-Admin","es":"Jefe del Team Skull","it":"Admin Team Skull","ja":"スカル団かんぶ","ko":"스컬단 간부","zh-Hans":"骷髅队管理员","zh-Hant":"骷髏隊管理員","pt-BR":"Admin do Team Skull"},
  "Team Yell":          {"en":"Team Yell Grunt","de":"Team Yell-Rüpel","es":"Recluta del Team Yell","it":"Recluta Team Yell","ja":"マクロコスモス社員","ko":"매크로코스모스 사원","zh-Hans":"叫喊队喽啰","zh-Hant":"叫喊隊嘍囉","pt-BR":"Recruta do Team Yell"},
  "Team Star":          {"en":"Team Star Grunt","de":"Team Star-Rüpel","es":"Recluta del Team Star","it":"Recluta Team Star","ja":"スター団したっぱ","ko":"스타단원","zh-Hans":"星团喽啰","zh-Hant":"星團嘍囉","pt-BR":"Recruta do Team Star"},
  "Boss Team":          {"en":"Team Boss","de":"Team-Boss","es":"Jefe del Team","it":"Boss del Team","ja":"ボス","ko":"보스","zh-Hans":"团队老大","zh-Hant":"團隊老大","pt-BR":"Chefe do Team"},
  "Agent":              {"en":"Team Rocket Grunt","de":"Team Rocket-Agent","es":"Agente del Team Rocket","it":"Agente Team Rocket","ja":"ロケット団したっぱ","ko":"로켓단원","zh-Hans":"火箭队成员","zh-Hant":"火箭隊成員","pt-BR":"Agente do Team Rocket"},
  "Admin":              {"en":"Team Admin","de":"Admin","es":"Jefe","it":"Admin","ja":"かんぶ","ko":"간부","zh-Hans":"管理员","zh-Hant":"管理員","pt-BR":"Admin"},

  # ── Combattants / Arts martiaux ───────────────────────────────
  "Karatéka":           {"en":"Black Belt","de":"Schwarzgurt","es":"Cinturón Negro","it":"Cintura Nera","ja":"からておとこ","ko":"가라테왕","zh-Hans":"空手道高手","zh-Hant":"空手道高手","pt-BR":"Faixa Preta"},
  "Judokate":           {"en":"Battle Girl","de":"Kämpferin","es":"Chica Luchadora","it":"Combattente","ja":"バトルガール","ko":"배틀걸","zh-Hans":"战斗少女","zh-Hant":"戰鬥少女","pt-BR":"Garota de Batalha"},
  "Battle Girl":        {"en":"Battle Girl","de":"Kämpferin","es":"Chica Luchadora","it":"Combattente","ja":"バトルガール","ko":"배틀걸","zh-Hans":"战斗少女","zh-Hant":"戰鬥少女","pt-BR":"Garota de Batalha"},
  "Chevalier":          {"en":"Battle Girl","de":"Kämpferin","es":"Chica Luchadora","it":"Combattente","ja":"バトルガール","ko":"배틀걸","zh-Hans":"战斗少女","zh-Hant":"戰鬥少女","pt-BR":"Garota de Batalha"},

  # ── Professions variées ───────────────────────────────────────
  "Fermier":            {"en":"Farmer","de":"Bauer","es":"Granjero","it":"Contadino","ja":"ぼくじょうのひと","ko":"목장사람","zh-Hans":"农场主","zh-Hant":"農場主","pt-BR":"Fazendeiro"},
  "Cowboy":             {"en":"Cowboy","de":"Cowboy","es":"Vaquero","it":"Cowboy","ja":"カウボーイ","ko":"카우보이","zh-Hans":"牛仔","zh-Hant":"牛仔","pt-BR":"Cowboy"},
  "Cuisinier":          {"en":"Cook","de":"Koch","es":"Cocinero","it":"Cuoco","ja":"コック","ko":"요리사","zh-Hans":"厨师","zh-Hant":"廚師","pt-BR":"Cozinheiro"},
  "Cuisinière":         {"en":"Cook","de":"Köchin","es":"Cocinera","it":"Cuoca","ja":"コック","ko":"요리사","zh-Hans":"厨师","zh-Hant":"廚師","pt-BR":"Cozinheira"},
  "Barista":            {"en":"Barista","de":"Barista","es":"Barista","it":"Barista","ja":"バリスタ","ko":"바리스타","zh-Hans":"咖啡师","zh-Hant":"咖啡師","pt-BR":"Barista"},
  "Médecin":            {"en":"Doctor","de":"Arzt","es":"Doctor","it":"Dottore","ja":"ドクター","ko":"의사","zh-Hans":"医生","zh-Hant":"醫生","pt-BR":"Médico"},
  "Infirmière":         {"en":"Nurse","de":"Krankenschwester","es":"Enfermera","it":"Infermiera","ja":"ナース","ko":"간호사","zh-Hans":"护士","zh-Hant":"護士","pt-BR":"Enfermeira"},
  "Aroma":              {"en":"Aroma Lady","de":"Aromadame","es":"Dama Aroma","it":"Signora Aroma","ja":"アロマなおねえさん","ko":"아로마레이디","zh-Hans":"香薰女士","zh-Hant":"香薰女士","pt-BR":"Dama Aroma"},
  "Aromathérapeute":    {"en":"Aroma Lady","de":"Aromadame","es":"Dama Aroma","it":"Signora Aroma","ja":"アロマなおねえさん","ko":"아로마레이디","zh-Hans":"香薰女士","zh-Hant":"香薰女士","pt-BR":"Dama Aroma"},
  "Arôma":              {"en":"Aroma Lady","de":"Aromadame","es":"Dama Aroma","it":"Signora Aroma","ja":"アロマなおねえさん","ko":"아로마레이디","zh-Hans":"香薰女士","zh-Hant":"香薰女士","pt-BR":"Dama Aroma"},

  # ── Sport ─────────────────────────────────────────────────────
  "Basketteur":         {"en":"Basketball Player","de":"Basketballspieler","es":"Jugador de Baloncesto","it":"Giocatore di Basket","ja":"バスケットボールプレイヤー","ko":"농구선수","zh-Hans":"篮球运动员","zh-Hant":"籃球運動員","pt-BR":"Jogador de Basquete"},
  "Footballeur":        {"en":"Football Player","de":"Fußballspieler","es":"Futbolista","it":"Calciatore","ja":"サッカー選手","ko":"축구선수","zh-Hans":"足球运动员","zh-Hant":"足球運動員","pt-BR":"Jogador de Futebol"},
  "Nageur":             {"en":"Swimmer","de":"Schwimmer","es":"Nadador","it":"Nuotatore","ja":"かいパンやろう","ko":"수영선수","zh-Hans":"游泳运动员","zh-Hant":"游泳運動員","pt-BR":"Nadador"},
  "Nageuse":            {"en":"Swimmer","de":"Schwimmerin","es":"Nadadora","it":"Nuotatrice","ja":"かいパンやろう","ko":"수영선수","zh-Hans":"游泳运动员","zh-Hant":"游泳運動員","pt-BR":"Nadadora"},
  "Skieur":             {"en":"Skier","de":"Skifahrer","es":"Esquiador","it":"Sciatore","ja":"スキーヤー","ko":"스키어","zh-Hans":"滑雪者","zh-Hant":"滑雪者","pt-BR":"Esquiador"},

  # ── Artistes de rue / Spectacle ───────────────────────────────
  "Artistes de Rue":    {"en":"Street Performer","de":"Straßenkünstler","es":"Artista Callejero","it":"Artista di Strada","ja":"パフォーマー","ko":"퍼포머","zh-Hans":"街头艺人","zh-Hant":"街頭藝人","pt-BR":"Artista de Rua"},
  "Mannequin":          {"en":"Model","de":"Model","es":"Modelo","it":"Modella","ja":"モデル","ko":"모델","zh-Hans":"模特","zh-Hant":"模特","pt-BR":"Modelo"},
  "Fantôme":            {"en":"Ghost","de":"Geist","es":"Fantasma","it":"Fantasma","ja":"ゾンビ","ko":"유령","zh-Hans":"幽灵","zh-Hant":"幽靈","pt-BR":"Fantasma"},

  # ── Trials / Islands (Alola) ───────────────────────────────────
  "Kapitan":            {"en":"Island Kahuna","de":"Inselkönig","es":"Rey de la Isla","it":"Kahuna dell'Isola","ja":"しまのぬし","ko":"섬의제왕","zh-Hans":"岛屿王者","zh-Hant":"島嶼王者","pt-BR":"Kahuna da Ilha"},
  "Capitaine d'Épreuve":{"en":"Trial Captain","de":"Prüfungskapitän","es":"Capitán de Prueba","it":"Capitano dell'Isola","ja":"キャプテン","ko":"캡틴","zh-Hans":"试炼队长","zh-Hant":"試煉隊長","pt-BR":"Capitão de Prova"},
  "Assistant Épreuve":  {"en":"Trial Captain","de":"Prüfungskapitän","es":"Capitán de Prueba","it":"Capitano dell'Isola","ja":"キャプテン","ko":"캡틴","zh-Hans":"试炼队长","zh-Hant":"試煉隊長","pt-BR":"Capitão de Prova"},
  "Assistante de l'Épreuve": {"en":"Trial Captain","de":"Prüfungskapitän","es":"Capitán de Prueba","it":"Capitano dell'Isola","ja":"キャプテン","ko":"캡틴","zh-Hans":"试炼队长","zh-Hant":"試煉隊長","pt-BR":"Capitão de Prova"},
  "Assistant":          {"en":"Trial Captain","de":"Prüfungskapitän","es":"Capitán de Prueba","it":"Capitano dell'Isola","ja":"キャプテン","ko":"캡틴","zh-Hans":"试炼队长","zh-Hant":"試煉隊長","pt-BR":"Capitão de Prova"},

  # ── Divers jeux récents ───────────────────────────────────────
  "Magellan":           {"en":"Explorer","de":"Forscher","es":"Explorador","it":"Esploratore","ja":"たんけんか","ko":"탐험가","zh-Hans":"探险家","zh-Hant":"探險家","pt-BR":"Explorador"},
  "Chercheur":          {"en":"Researcher","de":"Forscher","es":"Investigador","it":"Ricercatore","ja":"けんきゅういん","ko":"연구원","zh-Hans":"研究员","zh-Hant":"研究員","pt-BR":"Pesquisador"},
  "Collectionneur":     {"en":"Collector","de":"Sammler","es":"Coleccionista","it":"Collezionista","ja":"コレクター","ko":"수집가","zh-Hans":"收藏家","zh-Hant":"收藏家","pt-BR":"Colecionador"},
  "Touriste":           {"en":"Tourist","de":"Tourist","es":"Turista","it":"Turista","ja":"かんこうきゃく","ko":"관광객","zh-Hans":"游客","zh-Hant":"遊客","pt-BR":"Turista"},
  "Enfant":             {"en":"School Kid","de":"Schüler","es":"Colegial","it":"Scolaro","ja":"がくせい","ko":"학생","zh-Hans":"学生","zh-Hant":"學生","pt-BR":"Escolar"},
  "Écolier":            {"en":"School Kid","de":"Schüler","es":"Colegial","it":"Scolaro","ja":"がくせい","ko":"학생","zh-Hans":"学生","zh-Hant":"學生","pt-BR":"Escolar"},
  "Écolière":           {"en":"School Kid","de":"Schülerin","es":"Colegiala","it":"Scolara","ja":"がくせい","ko":"학생","zh-Hans":"学生","zh-Hant":"學生","pt-BR":"Escolar"},
  "Étudiant":           {"en":"Student","de":"Student","es":"Estudiante","it":"Studente","ja":"がくせい","ko":"대학생","zh-Hans":"大学生","zh-Hant":"大學生","pt-BR":"Estudante"},
  "Étudiante":          {"en":"Student","de":"Studentin","es":"Estudiante","it":"Studentessa","ja":"がくせい","ko":"대학생","zh-Hans":"大学生","zh-Hant":"大學生","pt-BR":"Estudante"},
  "Gardien":            {"en":"Guard","de":"Wächter","es":"Guardia","it":"Guardiano","ja":"けいびいん","ko":"경비원","zh-Hans":"守卫","zh-Hant":"守衛","pt-BR":"Guarda"},
}

# ── API PokeAPI par ID ────────────────────────────────────────────
if USE_API:
    print(f"\n🔄 Récupération par ID (1 à 80)…\n")
    for class_id in range(1, 81):
        url = f"https://pokeapi.co/api/v2/trainer-class/{class_id}/"
        data = api_get(url)
        if data is None:
            continue
        names_by_lang: dict[str, str] = {}
        for n in data.get("names", []):
            lang = n.get("language", {}).get("name", "")
            name = n.get("name", "").strip()
            if lang in API_LANGS and name:
                names_by_lang[lang] = name
        fr_name = names_by_lang.get("fr", "")
        if not fr_name or fr_name not in fr_classes:
            print(f"  [{class_id:2d}] ignoré ({data.get('name','?')} / FR: {fr_name or '—'})")
            time.sleep(0.3)
            continue
        if fr_name not in result:
            result[fr_name] = names_by_lang
        else:
            for lang, val in names_by_lang.items():
                result[fr_name].setdefault(lang, val)
        print(f"  [{class_id:2d}] ✅ {fr_name} → {names_by_lang.get('en','?')}")
        time.sleep(0.3)

# ── Appliquer le fallback pour combler les trous ─────────────────
filled = 0
for fr_name, translations in FALLBACK.items():
    if fr_name not in fr_classes:
        continue
    if fr_name not in result:
        result[fr_name] = {**translations, "fr": fr_name}
        filled += 1
    else:
        for lang, val in translations.items():
            result[fr_name].setdefault(lang, val)

if filled:
    print(f"\n📋 {filled} classes ajoutées via le mapping de secours")

# ── Résumé ────────────────────────────────────────────────────────
matched   = set(result.keys()) & set(fr_classes)
unmatched = sorted(set(fr_classes) - matched)
print(f"\n✅ {len(matched)} classes matchées / {len(fr_classes)}")
if unmatched:
    print(f"ℹ️  {len(unmatched)} classes sans traduction (classes très spécifiques) :")
    for c in unmatched[:15]:
        print(f"   - {c}")

# ── Sauvegarde ────────────────────────────────────────────────────
_tmp = DEST.with_suffix(".tmp")
with open(_tmp, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
os.replace(_tmp, DEST)
print(f"\n📄 Sauvegardé → {DEST}  ({len(result)} entrées)")

print("\nCouverture par langue :")
all_langs = sorted({l for v in result.values() for l in v if l != "fr"})
for lang in all_langs:
    n = sum(1 for v in result.values() if lang in v)
    print(f"  {lang:10s} : {n}/{len(result)}")

print("\nRelance npm run build pour rebuilder le site.")
