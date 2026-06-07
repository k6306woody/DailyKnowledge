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
from datetime import date, timedelta
from pathlib import Path

# ── 環境設定 ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent          # D:\AI\Claude_agent\daily-knowledge
DATA_DIR = ROOT / "data"
HISTORY_FILE = ROOT / "history.json"
LOG_FILE = ROOT / "logs" / "update.log"

LOG_FILE.parent.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

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

# ── 領域設定 ──────────────────────────────────────────────────────────────
DOMAIN_CONFIG = {
    "ai":     {"emoji": "🤖", "color": "#667eea", "label": "人工智慧"},
    "bio":    {"emoji": "🧬", "color": "#48bb78", "label": "生命科學"},
    "phys":   {"emoji": "⚛️",  "color": "#ed8936", "label": "物理科學"},
    "neuro":  {"emoji": "🧠", "color": "#9f7aea", "label": "神經科學"},
    "health": {"emoji": "🏥", "color": "#fc8181", "label": "醫療健康"},
    "space":  {"emoji": "🌌", "color": "#4299e1", "label": "天文宇宙"},
    "chem":   {"emoji": "🧪", "color": "#f6e05e", "label": "化學材料"},
    "tech":   {"emoji": "📶", "color": "#68d391", "label": "科技趣聞"},
    "ocean":  {"emoji": "🦈", "color": "#76e4f7", "label": "海洋生物"},
    "nature": {"emoji": "🐠", "color": "#fbd38d", "label": "自然生物"},
    "fin":    {"emoji": "💰", "color": "#f687b3", "label": "經濟金融"},
    "arch":   {"emoji": "🏛️", "color": "#a0aec0", "label": "建築環境"},
}

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

def call_claude(prompt, max_tokens=4000):
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        log.error(f"Anthropic API 錯誤: {e}")
        raise

# ── 產生卡片 ──────────────────────────────────────────────────────────────
PAPER_BATCHES = [
    [("ai","🤖","人工智慧/機器學習"), ("bio","🧬","生命科學/生物醫學"), ("phys","⚛️","物理/量子")],
    [("neuro","🧠","神經科學"), ("space","🌌","太空/天文"), ("tech","📶","自選：化學/材料/技術/海洋/經濟（domain 自選 chem/tech/ocean/fin/arch/health）")],
]

def _paper_prompt(today_str, paper_date, recent_str, domains):
    domain_list = "\n".join(f"{i+1}. {d[2]}（domain: {d[0]}）" for i,d in enumerate(domains))
    pid = paper_date[2:4] + paper_date[5:7]
    d0 = domains[0]
    color_map = {"ai":"#667eea","bio":"#48bb78","phys":"#ed8936","neuro":"#9f7aea",
                 "space":"#4299e1","tech":"#68d391","chem":"#f6e05e","ocean":"#76e4f7",
                 "fin":"#f687b3","arch":"#a0aec0","health":"#fc8181"}
    ex_color = color_map.get(d0[0],"#667eea")
    return f"""你是「每日新知」科普卡片編輯，為 {today_str}（arXiv 日期 {paper_date}）產生 3 張論文卡片。

已出現過的主題（請勿重複）：
{recent_str}

請從以下 3 個領域各選一篇真實的 2026 年 arXiv 論文：
{domain_list}

輸出純 JSON 陣列（不要有任何說明）：
[
  {{
    "id": "{d0[0]}-{pid}",
    "domain": "{d0[0]}",
    "day": "{today_str}",
    "author": "作者名 et al. 2026",
    "ref": "arXiv:2606.XXXXX",
    "url": "https://arxiv.org/abs/2606.XXXXX",
    "color": "{ex_color}",
    "title": {{"zh-TW":"繁體中文標題","en":"English Title","zh-CN":"简体中文","ja":"日本語","ko":"한국어"}},
    "tag":   {{"zh-TW":"{d0[1]} 人工智慧","en":"{d0[1]} AI","zh-CN":"{d0[1]} 人工智能","ja":"{d0[1]} 人工知能","ko":"{d0[1]} 인공지능"}},
    "tech":  {{"zh-TW":"技術說明（2句內）","en":"Tech explanation","zh-CN":"技术说明","ja":"技術説明","ko":"기술 설명"}},
    "plain": {{"zh-TW":"白話解釋（1-2句）","en":"Plain explanation","zh-CN":"白话解释","ja":"わかりやすく","ko":"쉬운 설명"}},
    "insight":{{"zh-TW":"💡 洞見","en":"💡 Insight","zh-CN":"💡 洞见","ja":"💡 洞察","ko":"💡 통찰"}}
  }}
]

重要：
- ref 用真實 arXiv ID（2606.XXXXX）
- color 用對應領域色碼（ai:#667eea, bio:#48bb78, phys:#ed8936, neuro:#9f7aea, space:#4299e1, chem:#f6e05e, tech:#68d391, ocean:#76e4f7, fin:#f687b3, arch:#a0aec0, health:#fc8181）
- 每個語言的 tech/plain/insight 各限 **1 句話**，絕對不要超過 50 個字
- JSON 字串值內禁止出現任何 ASCII 雙引號 "，需要引號請用「」或（）代替
- 只輸出 JSON 陣列，不加任何說明"""


def generate_cards_paper(date_info, recent_topics):
    paper_date = date_info["paper_date_str"]
    today_str = date_info["today_str"]
    recent_str = "\n".join(f"- {t}" for t in recent_topics[-20:])

    all_cards = []
    for batch_num, domains in enumerate(PAPER_BATCHES, 1):
        prompt = _paper_prompt(today_str, paper_date, recent_str, domains)
        raw = call_claude(prompt, max_tokens=8000)
        json_str = extract_json(raw)
        if not json_str:
            log.error(f"論文第{batch_num}批 raw 末尾: {raw[-200:]}")
            raise ValueError(f"論文第{batch_num}批 API 回傳無法解析:\n{raw[:300]}")
        try:
            cards = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning(f"論文第{batch_num}批 JSON 初次解析失敗: {e}，嘗試 repair...")
            try:
                repaired = repair_json_str(json_str)
                cards = json.loads(repaired)
                log.info(f"論文第{batch_num}批 repair 成功")
            except json.JSONDecodeError as e2:
                log.error(f"論文第{batch_num}批 JSON 仍無法解析: {e2}, 附近: {json_str[max(0,e.pos-80):e.pos+80]}")
                raise e2
        log.info(f"論文第{batch_num}批生成 {len(cards)} 張卡片")
        all_cards.extend(cards)

    log.info(f"論文共生成 {len(all_cards)} 張卡片")
    return all_cards


def _weekend_prompt(today_str, recent_str, batch, suffixes):
    suffix_list = "/".join(suffixes)
    return f"""你是「每日新知」科普卡片編輯，今天是 {today_str}（週末），要產生 3 張有趣科學新知卡片（第{batch}批）。

已出現過的主題（請勿重複）：
{recent_str}

請選 3 個 2025-2026 年真實的科學新發現或自然奇聞，涵蓋多元領域（與第{3-batch}批主題不重疊）：
- 自然生物（動物行為、演化、生態）
- 海洋生物（深海、珊瑚礁、新物種）
- 神經科學（大腦、記憶、感知）
- 天文宇宙（行星、星系、太空任務）
- 醫療健康（新療法、研究突破）
- 科技趣聞（材料、工程、發明）

每張卡片輸出 JSON，格式如下（輸出純 JSON 陣列，不要加任何說明）：
[
  {{
    "id": "nature-{today_str[2:4]}{today_str[5:7]}{suffixes[0]}",
    "domain": "nature",
    "day": "{today_str}",
    "author": "Nature / 2026",
    "ref": "Nature 2026",
    "url": "https://www.nature.com/",
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
- 每個領域用對應的 color（ai:#667eea, bio:#48bb78, phys:#ed8936, neuro:#9f7aea, health:#fc8181, space:#4299e1, chem:#f6e05e, tech:#68d391, ocean:#76e4f7, nature:#fbd38d, fin:#f687b3, arch:#a0aec0）
- url 盡量填真實文章連結（Nature / Science / arXiv / DOI）
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
        log.info(f"第{batch}批生成 {len(cards)} 張週末趣知卡片")
        all_cards.extend(cards)

    log.info(f"週末共生成 {len(all_cards)} 張卡片")
    return all_cards


# ── 產生 SVG 插圖（使用 gen_illustration.py）──────────────────────────────
try:
    from gen_illustration import generate_illus
    log.info("✅ 使用 gen_illustration.py 精美插圖")
except ImportError:
    log.warning("gen_illustration.py 不存在，使用簡易備用插圖")
    def generate_illus(card):
        domain = card.get("domain", "ai")
        cfg = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["ai"])
        color = cfg["color"]
        emoji = cfg["emoji"]
        label = cfg["label"]
        return (f'<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">'
                f'<rect width="200" height="120" fill="{color}22" rx="10"/>'
                f'<rect width="200" height="4" rx="2" fill="{color}"/>'
                f'<text x="100" y="70" text-anchor="middle" font-size="42">{emoji}</text>'
                f'<text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">{label}</text>'
                f'</svg>')


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
        card["illus"] = generate_illus(card)
        output["cards"].append(card)

    out_path = DATA_DIR / f"{today_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info(f"已寫出 {out_path} ({out_path.stat().st_size // 1024}KB)")
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
    log.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="補歷史資料用，格式 YYYY-MM-DD", default=None)
    parser.add_argument("--force", action="store_true", help="強制重新生成（即使已存在）")
    args = parser.parse_args()
    main(override_date=args.date, force=args.force)
