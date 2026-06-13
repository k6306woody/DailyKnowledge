#!/usr/bin/env python3
"""
daily_update.py — 每日知識卡片自動更新腳本
- 平日（週一~週五）：抓 arXiv 最新論文
- 假日（週六~週日）：生成科學趣知卡片
- 全自動執行，無 input()，API key 從環境變數讀取
- 輸出：data/YYYY-MM-DD.json + 更新 history.json
"""

import os
import sys
import json
import re
import logging
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

# ── 環境設定 ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent          # D:\AI\Claude_agent\daily-knowledge
DATA_DIR = ROOT / "data"
HISTORY_FILE = ROOT / "history.json"
LOG_FILE = ROOT / "logs" / "update.log"

LOG_FILE.parent.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# 強制 stdout 用 UTF-8，避免 Windows cp950 無法輸出 emoji 造成 log 錯誤
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Anthropic API ──────────────────────────────────────────────────────────
try:
    import anthropic
except ImportError:
    log.error("請先執行: pip install anthropic")
    sys.exit(1)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    log.error("未設定 ANTHROPIC_API_KEY 環境變數")
    sys.exit(1)

client = anthropic.Anthropic(api_key=API_KEY)

# ── 領域設定（正規 11 類，單一真相來源）────────────────────────────────────
# ⚠️ 卡片的 domain 只能是以下 11 個 key 之一。新增/修改分類請改這裡。
DOMAIN_CONFIG = {
    "ai":      {"emoji": "🤖", "color": "#2a9d8f", "label": "AI與機器人"},
    "bio":     {"emoji": "🧬", "color": "#52b788", "label": "生命科學"},
    "neuro":   {"emoji": "🧠", "color": "#6a1b9a", "label": "神經科學"},
    "health":  {"emoji": "🏥", "color": "#b71c1c", "label": "醫療健康"},
    "phys":    {"emoji": "⚛️",  "color": "#4a7bbf", "label": "物理量子"},
    "chem":    {"emoji": "🧪", "color": "#bf5b9b", "label": "化學材料"},
    "space":   {"emoji": "🌌", "color": "#1a237e", "label": "天文宇宙"},
    "climate": {"emoji": "🌍", "color": "#e8590c", "label": "地球氣候"},
    "nature":  {"emoji": "🐠", "color": "#2e7d32", "label": "自然生態"},
    "tech":    {"emoji": "📶", "color": "#00695c", "label": "科技工程"},
    "human":   {"emoji": "🏛️", "color": "#a0aec0", "label": "人文社會"},
}

# 正規 domain 集合 + 別名對照（強制把舊/自創 domain 收斂到正規 11 類）
CANONICAL_DOMAINS = set(DOMAIN_CONFIG.keys())
DOMAIN_ALIAS = {
    "robot": "ai", "robotics": "ai",
    "quantum": "phys",
    "med": "health", "medicine": "health", "medical": "health",
    "ocean": "nature", "marine": "nature",
    "fin": "human", "finance": "human", "econ": "human", "economics": "human",
    "arch": "human", "architecture": "human",
    "earth": "climate", "environment": "climate",
}

def normalize_domain(domain: str) -> str:
    """把任意 domain 收斂到正規 11 類；未知則記 log 並退回 'tech'。"""
    d = (domain or "").strip().lower()
    if d in CANONICAL_DOMAINS:
        return d
    if d in DOMAIN_ALIAS:
        log.info(f"  domain 正規化：{d} → {DOMAIN_ALIAS[d]}")
        return DOMAIN_ALIAS[d]
    log.warning(f"  未知 domain '{domain}'，fallback → tech")
    return "tech"

def apply_canonical(card: dict) -> dict:
    """正規化卡片 domain 並用正規色覆蓋 color（確保色條/標籤同色）。"""
    dom = normalize_domain(card.get("domain", ""))
    card["domain"] = dom
    card["color"] = DOMAIN_CONFIG[dom]["color"]
    return card

LANGS = ["zh-TW", "en", "zh-CN", "ja", "ko"]

# ── 日期邏輯 ──────────────────────────────────────────────────────────────
def get_date_info(override_date=None):
    today = date.fromisoformat(override_date) if override_date else date.today()
    wd = today.weekday()  # 0=Mon, 6=Sun
    is_weekend = wd >= 5

    if wd == 0:
        paper_date = today - timedelta(days=3)  # 週一用上週五
    elif wd == 6:
        paper_date = today - timedelta(days=2)  # 週日用上週五
    elif wd == 5:
        paper_date = today - timedelta(days=1)  # 週六用週五
    else:
        paper_date = today

    return {
        "today": today,
        "today_str": today.isoformat(),
        "weekday": wd,
        "is_weekend": is_weekend,
        "paper_date": paper_date,
        "paper_date_str": paper_date.isoformat(),
        "mode": "weekend" if is_weekend else "paper",
    }

# ── 歷史紀錄 ──────────────────────────────────────────────────────────────
def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}

def get_recent_topics(history, n=30):
    """回傳最近 n 天出現過的 topic 清單，避免重複"""
    topics = []
    for entry in history["entries"][-n:]:
        topics.extend(entry.get("topics", []))
    return topics

def save_history(history, date_str, mode, topics):
    history["entries"].append({
        "date": date_str,
        "mode": mode,
        "topics": topics,
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    log.info(f"history.json 已更新 ({date_str})")


# ── Git 自動推送 ──────────────────────────────────────────────────────────
def git_push(date_str: str):
    """將新產生的 JSON + history.json commit 並 push 到 GitHub Pages"""
    import subprocess

    def run(cmd, **kw):
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, **kw)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    try:
        log.info("── Git 自動推送 ──")
        # 確認有無遠端
        run(["git", "remote", "get-url", "origin"])

        # stage：當天 JSON + history.json
        run(["git", "add",
             f"data/{date_str}.json",
             "history.json"])

        # 確認有東西要 commit
        status = run(["git", "status", "--porcelain"])
        if not status:
            log.info("  沒有變更，跳過 commit")
            return

        run(["git", "commit", "-m",
             f"data: auto-update {date_str} ({len(status.splitlines())} files)"])
        log.info("  ✓ commit 完成")

        run(["git", "push"])
        log.info("  ✓ push 完成 → GitHub Pages 已更新")

    except Exception as e:
        log.error(f"  ✗ git push 失敗：{e}")
        log.error("    請手動執行：git add data/ history.json && git commit -m '...' && git push")


# ── Anthropic API 呼叫 ────────────────────────────────────────────────────
def sanitize_json(text):
    # Fix common JSON issues from Claude output
    # Use chr() to avoid Python 3.12+ syntax error with smart quotes
    text = text.replace(chr(0x201C), chr(0x300C))   # left double quote
    text = text.replace(chr(0x201D), chr(0x300D))   # right double quote
    text = text.replace(chr(0x2018), "'")
    text = text.replace(chr(0x2019), "'")
    return text

def repair_json_str(raw_json):
    """Try to fix JSON strings with unescaped double quotes."""
    result = []
    in_string = False
    escape_next = False
    i = 0
    while i < len(raw_json):
        ch = raw_json[i]
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == chr(92):  # backslash
            result.append(ch)
            escape_next = True
        elif ch == chr(34):  # double quote
            if not in_string:
                in_string = True
                result.append(ch)
            else:
                rest = raw_json[i+1:].lstrip()
                if rest and rest[0] in (",", "}", "]", ":"):
                    in_string = False
                    result.append(ch)
                else:
                    result.append(chr(0xFF02))  # fullwidth quotation mark
        else:
            result.append(ch)
        i += 1
    return "".join(result)

def extract_json(raw):
    """從 Claude 回傳文字中取出 JSON 陣列，容忍 markdown code block 包裝"""
    # 去掉 ```json 或 ``` 開頭與結尾
    text = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    # 找第一個 [ 到最後一個 ]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        return sanitize_json(text[start:end+1])
    return None

def call_claude(prompt, max_tokens=4000, retries=3, base_delay=15):
    """呼叫 Claude API，含 timeout + 指數退避 retry"""
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                timeout=120.0,   # 2 分鐘 hard timeout，防止卡死
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)  # 15s → 30s → 60s
                log.warning(f"  API 第 {attempt+1} 次失敗，{wait}秒後重試：{e}")
                time.sleep(wait)
            else:
                log.error(f"  API 連續 {retries} 次失敗：{e}")
                raise

# ── arXiv API 抓真實論文 ──────────────────────────────────────────────────
# domain → arXiv category 對應
ARXIV_CATS = {
    "ai":      "cs.AI cs.LG cs.CL cs.RO",
    "bio":     "q-bio.GN q-bio.CB q-bio.MN",
    "neuro":   "q-bio.NC cs.NE",
    "health":  "q-bio.TO q-bio.QM",
    "phys":    "cond-mat.supr-con cond-mat.mes-hall quant-ph",
    "chem":    "cond-mat.mtrl-sci physics.chem-ph",
    "space":   "astro-ph.GA astro-ph.EP astro-ph.HE",
    "climate": "physics.ao-ph physics.geo-ph",
    "nature":  "q-bio.PE q-bio.OT",
    "tech":    "eess.SP cs.SY eess.IV",
    "human":   "econ.GN q-fin.GN cs.CY",
}

def fetch_arxiv_papers(domain: str, paper_date: str, n: int = 5) -> list[dict]:
    """
    從 arXiv API 抓指定領域的最新論文（paper_date 前後 3 天）。
    回傳 list of {arxiv_id, title, authors, abstract, url, submitted}
    """
    cats = ARXIV_CATS.get(domain, "cs.AI")
    cat_query = "(" + " OR ".join(f"cat:{c}" for c in cats.split()) + ")"

    # 以 paper_date 為中心建立日期窗（前 4 天 ~ 當天），讓「週一抓上週五／補歷史」真正生效
    date_clause = ""
    try:
        pd = date.fromisoformat(paper_date)
        lo = (pd - timedelta(days=4)).strftime("%Y%m%d") + "0000"
        hi = pd.strftime("%Y%m%d") + "2359"
        date_clause = f" AND submittedDate:[{lo} TO {hi}]"
    except Exception:
        pass  # paper_date 解析失敗就退回純最新

    def _query(search_query):
        params = urllib.parse.urlencode({
            "search_query": search_query,
            "start": 0,
            "max_results": n,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        api_url = f"https://export.arxiv.org/api/query?{params}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "DailyKnowledge/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            xml_data = r.read()
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        out = []
        for entry in root.findall("atom:entry", ns):
            arxiv_id = entry.find("atom:id", ns).text.strip().split("/abs/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            authors = [a.find("atom:name", ns).text.strip()
                       for a in entry.findall("atom:author", ns)]
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            published = entry.find("atom:published", ns).text[:10]
            out.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors[:3],
                "abstract": abstract[:600],
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "ref": f"arXiv:{arxiv_id}",
                "submitted": published,
            })
        return out

    log.info(f"  arXiv fetch: domain={domain} cats={cats} window={date_clause or '最新'}")
    try:
        results = _query(cat_query + date_clause)
        # 日期窗內無結果 → 放寬退回純最新，避免空手而回
        if not results and date_clause:
            log.info(f"  {domain} 日期窗內無論文，放寬抓最新")
            results = _query(cat_query)
        log.info(f"  arXiv fetched {len(results)} papers for {domain}")
        return results
    except Exception as e:
        log.warning(f"  arXiv fetch failed for {domain}: {e}")
        return []


# ── 產生卡片 ──────────────────────────────────────────────────────────────
# 平日 arXiv 固定 6 類（emoji/label 取自 DOMAIN_CONFIG，單一真相來源）
_PAPER_KEYS = ["ai", "bio", "phys", "neuro", "space", "tech"]
PAPER_DOMAINS = [(k, DOMAIN_CONFIG[k]["emoji"], DOMAIN_CONFIG[k]["label"]) for k in _PAPER_KEYS]

# 顏色查表由 DOMAIN_CONFIG 導出（避免重複定義 / 不一致）
COLOR_MAP = {k: v["color"] for k, v in DOMAIN_CONFIG.items()}

def _summarize_paper_prompt(today_str, domain, emoji, domain_label, paper, card_id, recent_str):
    """讓 Claude 把真實論文的 title+abstract 轉成多語言卡片 JSON"""
    color = COLOR_MAP.get(domain, "#667eea")
    author_str = ", ".join(paper["authors"]) + " et al." if paper["authors"] else "et al."
    return f"""你是「每日新知」科普卡片編輯。請把下列真實 arXiv 論文摘要轉化成一張多語言知識卡片（含 SVG 插圖）。

【論文資料】
標題（英）：{paper["title"]}
作者：{author_str}
arXiv ID：{paper["arxiv_id"]}
摘要（英）：{paper["abstract"]}

【卡片規格】
- id: "{card_id}"
- domain: "{domain}"
- day: "{today_str}"
- color: "{color}"

【語言要求】
- title：各語言翻譯論文標題（可意譯讓非專業讀者理解）
- tag：用 {emoji} 開頭，各語言填「{emoji} {domain_label}」類的領域標籤
- tech：2-3句，技術性說明這篇論文做了什麼、方法是什麼
- plain：5-8句，用生動比喻+舉例，讓完全不懂的人也能理解，要有「為什麼重要」
- insight：💡 開頭，1句洞見或啟示

【SVG 插圖規格（illus 欄位）】
- viewBox="0 0 340 160"，最多 12 個圖形元素
- 禁止 <defs>/<linearGradient>/<filter>/<clipPath>/<text>
- 背景：<rect width="340" height="160" fill="{color}18"/>
- 主色 {color}，可搭配 1-2 個輔色
- 用幾何圖形象徵論文核心概念

【已出現過的主題（勿重複）】
{recent_str}

輸出純 JSON 物件（不要陣列，不要說明）：
{{
  "id": "{card_id}",
  "domain": "{domain}",
  "day": "{today_str}",
  "author": "{author_str}",
  "ref": "{paper['ref']}",
  "url": "{paper['url']}",
  "color": "{color}",
  "illus": "<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 340 160\\">...</svg>",
  "title":   {{"zh-TW":"","en":"","zh-CN":"","ja":"","ko":""}},
  "tag":     {{"zh-TW":"{emoji} {domain_label}","en":"{emoji} {domain_label}","zh-CN":"{emoji} {domain_label}","ja":"{emoji} {domain_label}","ko":"{emoji} {domain_label}"}},
  "tech":    {{"zh-TW":"","en":"","zh-CN":"","ja":"","ko":""}},
  "plain":   {{"zh-TW":"","en":"","zh-CN":"","ja":"","ko":""}},
  "insight": {{"zh-TW":"","en":"","zh-CN":"","ja":"","ko":""}}
}}

重要：JSON 字串內禁止出現 ASCII 雙引號，需要引號請用「」代替。只輸出 JSON，不加說明。"""


def generate_cards_paper(date_info, recent_topics):
    today_str = date_info["today_str"]
    paper_date = date_info["paper_date_str"]
    recent_str = "\n".join(f"- {t}" for t in recent_topics[-20:])
    pid = today_str[2:4] + today_str[5:7] + today_str[8:10]  # YYMMDD

    # ── 斷點恢復：讀取 partial save ──────────────────────────────────
    partial_path = DATA_DIR / f"{today_str}.partial.json"
    all_cards = []
    done_domains = set()
    if partial_path.exists():
        try:
            with open(partial_path, encoding="utf-8") as f:
                partial = json.load(f)
            all_cards = partial.get("cards", [])
            done_domains = {c["domain"] for c in all_cards}
            log.info(f"  ↩️  發現斷點紀錄，已完成 {done_domains}，從斷點繼續")
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────

    used_arxiv_ids = {c.get("ref", "").replace("arXiv:", "") for c in all_cards}

    for domain, emoji, domain_label in PAPER_DOMAINS:
        if domain in done_domains:
            log.info(f"  ✓ {domain} 已有資料，跳過")
            continue
        log.info(f"\n── 處理領域: {domain} ({emoji} {domain_label}) ──")

        # 1. 從 arXiv 抓真實論文
        papers = fetch_arxiv_papers(domain, paper_date, n=8)
        time.sleep(1)  # arXiv rate limit

        # 選一篇未用過的
        chosen = None
        for p in papers:
            if p["arxiv_id"] not in used_arxiv_ids:
                chosen = p
                used_arxiv_ids.add(p["arxiv_id"])
                break

        if not chosen:
            log.warning(f"  找不到未用過的 {domain} 論文，跳過")
            continue

        log.info(f"  選用: {chosen['arxiv_id']} — {chosen['title'][:60]}")

        # 2. 讓 Claude 摘要成卡片
        card_id = f"{domain}-{pid}"
        prompt = _summarize_paper_prompt(today_str, domain, emoji, domain_label,
                                          chosen, card_id, recent_str)
        raw = call_claude(prompt, max_tokens=4000)

        # 解析 JSON 物件（不是陣列）
        text = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        text = re.sub(r'\s*```$', '', text.strip())
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            log.error(f"  {domain} 無法找到 JSON 物件，raw: {raw[:200]}")
            continue
        json_str = sanitize_json(text[start:end+1])
        try:
            card = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning(f"  {domain} JSON 解析失敗，嘗試 repair: {e}")
            try:
                card = json.loads(repair_json_str(json_str))
            except Exception as e2:
                log.error(f"  {domain} repair 失敗: {e2}")
                continue

        # 確保 url/ref 正確（用 arXiv API 的值覆蓋）
        card["url"] = chosen["url"]
        card["ref"] = chosen["ref"]
        card["author"] = ", ".join(chosen["authors"][:2]) + (" et al." if len(chosen["authors"]) > 1 else "")

        apply_canonical(card)  # 強制 domain 正規化 + 正規色
        log.info(f"  ✓ 卡片生成: {card.get('id')} — {card.get('title',{}).get('zh-TW','')[:40]}")
        all_cards.append(card)

        # ── Partial save：每張卡片完成後立即存檔，斷點可續接 ──────────
        try:
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({"date": today_str, "partial": True, "cards": all_cards}, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning(f"  partial save 失敗（不影響主流程）：{e}")
        # ─────────────────────────────────────────────────────────────

        time.sleep(0.5)

    log.info(f"\n論文共生成 {len(all_cards)} 張卡片")
    return all_cards


def _weekend_prompt(today_str, recent_str, batch, suffixes):
    suffix_list = "/".join(suffixes)
    return f"""你是「每日新知」科普卡片編輯，今天是 {today_str}（週末），要產生 3 張有趣科學新知卡片（第{batch}批）。

已出現過的主題（請勿重複）：
{recent_str}

請選 3 個 2025-2026 年真實的科學新發現或自然奇聞，涵蓋多元領域（與第{3-batch}批主題不重疊）。
⚠️ domain 欄位「只能」是以下 11 個 key 之一，禁止自創其他 domain：
- nature（自然生態：動物行為、演化、生態、海洋生物）
- neuro（神經科學：大腦、記憶、感知）
- space（天文宇宙：行星、星系、太空任務）
- health（醫療健康：新療法、疾病、醫學）
- tech（科技工程：材料、工程、發明）
- ai（AI與機器人）
- bio（生命科學：基因、細胞）
- phys（物理量子）
- chem（化學材料）
- climate（地球氣候：氣候、環境、地球科學）
- human（人文社會：經濟、財經、建築、社會）

每張卡片輸出 JSON，格式如下（輸出純 JSON 陣列，不要加任何說明）：
[
  {{
    "id": "nature-{today_str[2:4]}{today_str[5:7]}{suffixes[0]}",
    "domain": "nature",
    "day": "{today_str}",
    "author": "Zhang et al. / Nature 2026",
    "ref": "Nature 2026",
    "url": "https://doi.org/10.1038/...",
    "color": "#fbd38d",
    "title": {{"zh-TW": "繁體中文標題","en": "English Title","zh-CN": "简体中文","ja": "日本語","ko": "한국어"}},
    "tag": {{"zh-TW": "🐠 自然生物","en": "🐠 Nature","zh-CN": "🐠 自然生物","ja": "🐠 自然生物","ko": "🐠 자연 생물"}},
    "tech": {{"zh-TW": "科學說明（2句內）","en": "Science explanation","zh-CN": "科学说明","ja": "科学的説明","ko": "과학적 설명"}},
    "plain": {{"zh-TW": "白話解釋（1-2句）","en": "Plain explanation","zh-CN": "白话解释","ja": "わかりやすく","ko": "쉬운 설명"}},
    "insight": {{"zh-TW": "💡 洞見（1句）","en": "💡 Insight","zh-CN": "💡 洞见","ja": "💡 洞察","ko": "💡 통찰"}}
  }}
]

重要：
- id 後綴依序用 {suffix_list}
- domain 只能用這 11 個 key：ai, bio, neuro, health, phys, chem, space, climate, nature, tech, human
- 每個領域用對應的 color（ai:#2a9d8f, bio:#52b788, neuro:#6a1b9a, health:#b71c1c, phys:#4a7bbf, chem:#bf5b9b, space:#1a237e, climate:#e8590c, nature:#2e7d32, tech:#00695c, human:#a0aec0）
- url 必須填具體文章的直達連結，格式優先：
    arXiv: https://arxiv.org/abs/XXXX.XXXXX
    DOI:   https://doi.org/10.xxxx/xxxxxx
    Nature: https://www.nature.com/articles/s41586-xxxx-xxxx-x
    Science: https://www.science.org/doi/10.1126/science.xxxxxxx
    絕對不要填期刊首頁（如 https://www.nature.com/ 或 https://www.science.org/）
- ref 填期刊縮寫 + 年份（如 "Nature 2026"、"Science 2025"）
- author 填真實第一作者姓氏（如 "Zhang et al. / Nature 2026"）
- JSON 字串值內禁止出現任何 ASCII 雙引號 "，需要引號請用「」或（）代替
- 只輸出 JSON 陣列，不要有任何說明文字"""


def generate_cards_weekend(date_info, recent_topics):
    today_str = date_info["today_str"]
    recent_str = "\n".join(f"- {t}" for t in recent_topics[-20:])

    all_cards = []
    for batch, suffixes in [(1, ["a","b","c"]), (2, ["d","e","f"])]:
        prompt = _weekend_prompt(today_str, recent_str, batch, suffixes)
        raw = call_claude(prompt, max_tokens=6000)
        json_str = extract_json(raw)
        if not json_str:
            log.error(f"第{batch}批 raw 末尾: {raw[-200:]}")
            raise ValueError(f"第{batch}批 API 回傳內容無法解析為 JSON:\n{raw[:300]}")
        try:
            cards = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning(f"第{batch}批 JSON 初次解析失敗: {e}，嘗試 repair...")
            try:
                repaired = repair_json_str(json_str)
                cards = json.loads(repaired)
                log.info(f"第{batch}批 repair 成功")
            except json.JSONDecodeError as e2:
                log.error(f"第{batch}批 JSON 仍無法解析: {e2}")
                log.error(f"問題附近: {json_str[max(0,e.pos-100):e.pos+100]}")
                raise e2
        for c in cards:
            apply_canonical(c)  # 強制 domain 正規化 + 正規色
        log.info(f"第{batch}批生成 {len(cards)} 張週末趣知卡片")
        all_cards.extend(cards)

    log.info(f"週末共生成 {len(all_cards)} 張卡片")
    return all_cards


# ── 產生 AI 客製化 SVG 插圖 ────────────────────────────────────────────────
def _fallback_illus(card):
    """Domain-based fallback SVG when API call fails"""
    domain = card.get("domain", "ai")
    cfg = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["ai"])
    color = cfg["color"]
    emoji = cfg["emoji"]
    label = cfg["label"]
    return (f'<svg viewBox="0 0 340 160" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="340" height="160" fill="{color}18" rx="12"/>'
            f'<rect width="340" height="5" rx="2" fill="{color}"/>'
            f'<text x="170" y="97" text-anchor="middle" font-size="56">{emoji}</text>'
            f'<text x="12" y="150" font-size="11" fill="{color}" font-weight="700" '
            f'font-family="sans-serif">{label}</text>'
            f'</svg>')

def generate_illus(card):
    """Call Claude API to generate a paper-specific SVG illustration (340x160)."""
    title_zh = card.get("title", {}).get("zh-TW", "")
    plain_zh = card.get("plain", {}).get("zh-TW", "")
    domain   = card.get("domain", "ai")
    color    = card.get("color", DOMAIN_CONFIG.get(domain, {}).get("color", "#667eea"))

    prompt = f"""設計一張科普插圖 SVG（340×160），視覺呈現以下概念：

主題：{title_zh}
概念：{plain_zh[:80]}
主色：{color}

【嚴格規範】
1. 開頭直接輸出 <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 160">
2. 最多使用 12 個圖形元素（circle/rect/line/polygon/path）
3. 禁止 <defs>、<linearGradient>、<radialGradient>、<filter>、<clipPath>（這些讓 SVG 太長）
4. 背景：<rect width="340" height="160" fill="{color}18"/>
5. 主色 {color}，可加 1-2 個搭配色
6. 禁止任何文字元素（<text>）
7. 最後一行必須是 </svg>
8. 不加任何說明文字，只輸出 SVG"""

    try:
        raw = call_claude(prompt, max_tokens=2000)
        # Strip markdown code fences (```svg ... ``` or ```xml ... ```)
        text = re.sub(r'^```[a-z]*\s*', '', raw.strip(), flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text.strip())
        # Extract <svg>...</svg>
        start = text.find("<svg")
        end = text.rfind("</svg>")
        if start != -1 and end != -1:
            svg = text[start:end+6]
            # Ensure viewBox
            if 'viewBox' not in svg:
                svg = svg.replace('<svg', '<svg viewBox="0 0 340 160"', 1)
            log.info(f"插圖生成成功 ({card.get('id')}, {len(svg)}B)")
            return svg
        else:
            log.warning(f"SVG 提取失敗，使用備用插圖 ({card.get('id')})")
            log.debug(f"Raw output: {raw[:200]}")
            return _fallback_illus(card)
    except Exception as e:
        log.warning(f"插圖 API 失敗 ({card.get('id')}): {e}，使用備用插圖")
        return _fallback_illus(card)


# ── 寫出 JSON ─────────────────────────────────────────────────────────────
def write_json(date_info, cards):
    today_str = date_info["today_str"]
    output = {
        "date": today_str,
        "mode": date_info["mode"],
        "paper_date": date_info["paper_date_str"],
        "generated_at": str(date.today()),
        "cards": [],
    }

    for card in cards:
        # 若卡片 prompt 已包含 illus（新流程），直接用；否則才另外呼叫 API
        if not card.get("illus"):
            card["illus"] = generate_illus(card)
        output["cards"].append(card)

    out_path = DATA_DIR / f"{today_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info(f"已寫出 {out_path} ({out_path.stat().st_size // 1024}KB)")

    # 清理 partial save 檔
    partial_path = DATA_DIR / f"{today_str}.partial.json"
    if partial_path.exists():
        partial_path.unlink()
        log.info(f"已清理 {partial_path.name}")

    return out_path


# ── 主程式 ────────────────────────────────────────────────────────────────
def main(override_date=None, force=False):
    log.info("=" * 60)
    log.info("每日新知自動更新開始")

    date_info = get_date_info(override_date)
    log.info(f"日期：{date_info['today_str']} | 模式：{date_info['mode']} | paper_date：{date_info['paper_date_str']}")

    history = load_history()
    recent_topics = get_recent_topics(history)

    # 檢查是否已更新（--force 可跳過）
    existing = [e for e in history["entries"] if e.get("date") == date_info["today_str"]]
    if existing and not force:
        log.info(f"{date_info['today_str']} 已更新過，跳過（加 --force 可強制重新生成）")
        return

    # 產生卡片
    if date_info["is_weekend"]:
        cards = generate_cards_weekend(date_info, recent_topics)
    else:
        cards = generate_cards_paper(date_info, recent_topics)

    # 寫出 JSON
    out_path = write_json(date_info, cards)

    # 更新 history
    topics = [c["title"]["zh-TW"] for c in cards]
    save_history(history, date_info["today_str"], date_info["mode"], topics)

    log.info(f"✅ 完成！{len(cards)} 張卡片已儲存至 {out_path}")

    # ── 自動 git push 更新網站 ───────────────────────────────────────────
    git_push(date_info["today_str"])

    # ── Instagram 自動發文（需設定 IG_ACCESS_TOKEN + IG_BUSINESS_ID）────
    if os.environ.get("IG_ACCESS_TOKEN") and os.environ.get("IG_BUSINESS_ID"):
        try:
            sys.path.insert(0, str(ROOT))
            from scripts.ig_poster import post_daily_card
            best_card = cards[0]   # 預設發第一張（ai 領域）
            post_daily_card(best_card, date_info["today_str"])
        except Exception as e:
            log.error(f"Instagram 發文失敗（不影響主流程）：{e}")
    else:
        log.info("IG_ACCESS_TOKEN / IG_BUSINESS_ID 未設定，跳過 Instagram 發文")

    log.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="補歷史資料用，格式 YYYY-MM-DD", default=None)
    parser.add_argument("--force", action="store_true", help="強制重新生成（即使已存在）")
    args = parser.parse_args()
    main(override_date=args.date, force=args.force)
