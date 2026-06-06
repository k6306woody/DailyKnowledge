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
def get_date_info():
    today = date.today()
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
def call_claude(prompt, max_tokens=4000):
    try:
        msg = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        log.error(f"Anthropic API 錯誤: {e}")
        raise

# ── 產生卡片 ──────────────────────────────────────────────────────────────
def generate_cards_paper(date_info, recent_topics):
    paper_date = date_info["paper_date_str"]
    today_str = date_info["today_str"]
    recent_str = "\n".join(f"- {t}" for t in recent_topics[-20:])

    prompt = f"""你是「每日新知」科普卡片編輯，今天要為 {today_str}（arXiv 日期 {paper_date}）產生 6 張論文卡片。

已出現過的主題（請勿重複）：
{recent_str}

請從以下領域各選一篇真實的 2026 年 arXiv 論文：
1. 人工智慧 / 機器學習（domain: ai）
2. 生命科學 / 生物醫學（domain: bio）
3. 物理 / 量子（domain: phys）
4. 神經科學（domain: neuro）
5. 太空 / 天文（domain: space）
6. 自選：化學/材料/技術/海洋/經濟（domain: chem/tech/ocean/fin/arch）

每張卡片輸出 JSON，格式如下（輸出純 JSON 陣列，不要加任何說明）：
[
  {{
    "id": "ai-{paper_date[2:4]}{paper_date[5:7]}",
    "domain": "ai",
    "day": "{today_str}",
    "author": "作者名 et al. 2026",
    "ref": "arXiv:2606.XXXXX",
    "url": "https://arxiv.org/abs/2606.XXXXX",
    "color": "#667eea",
    "title": {{
      "zh-TW": "繁體中文標題",
      "en": "English Title",
      "zh-CN": "简体中文标题",
      "ja": "日本語タイトル",
      "ko": "한국어 제목"
    }},
    "tag": {{
      "zh-TW": "🤖 人工智慧",
      "en": "🤖 Artificial Intelligence",
      "zh-CN": "🤖 人工智能",
      "ja": "🤖 人工知能",
      "ko": "🤖 인공지능"
    }},
    "tech": {{
      "zh-TW": "技術說明（2-3句）",
      "en": "Technical explanation (2-3 sentences)",
      "zh-CN": "技术说明（2-3句）",
      "ja": "技術説明（2〜3文）",
      "ko": "기술 설명 (2-3문장)"
    }},
    "plain": {{
      "zh-TW": "白話解釋（1-2句，生活化）",
      "en": "Plain explanation (1-2 sentences)",
      "zh-CN": "白话解释（1-2句）",
      "ja": "わかりやすい説明（1〜2文）",
      "ko": "쉬운 설명 (1-2문장)"
    }},
    "insight": {{
      "zh-TW": "💡 洞見（對未來的影響）",
      "en": "💡 Insight",
      "zh-CN": "💡 洞见",
      "ja": "💡 洞察",
      "ko": "💡 통찰"
    }}
  }}
]

重要：
- ref 必須是真實存在的 arXiv ID 格式（2606.XXXXX 或 2605.XXXXX）
- 每個領域用對應的 color（ai:#667eea, bio:#48bb78, phys:#ed8936, neuro:#9f7aea, space:#4299e1, chem:#f6e05e, tech:#68d391, ocean:#76e4f7, fin:#f687b3, arch:#a0aec0）
- 英文字串中的撇號寫 ' 即可（這是 JSON，不是 JS）
- 只輸出 JSON 陣列，不要有任何說明文字"""

    raw = call_claude(prompt, max_tokens=6000)

    # 取出 JSON 部分
    json_match = re.search(r'\[[\s\S]*\]', raw)
    if not json_match:
        raise ValueError(f"API 回傳內容無法解析為 JSON:\n{raw[:500]}")

    cards = json.loads(json_match.group())
    log.info(f"生成 {len(cards)} 張論文卡片")
    return cards


def generate_cards_weekend(date_info, recent_topics):
    today_str = date_info["today_str"]
    recent_str = "\n".join(f"- {t}" for t in recent_topics[-20:])

    prompt = f"""你是「每日新知」科普卡片編輯，今天是 {today_str}（週末），要產生 6 張有趣科學新知卡片。

已出現過的主題（請勿重複）：
{recent_str}

請選 6 個 2025-2026 年真實的科學新發現或自然奇聞，涵蓋多元領域：
- 自然生物（動物行為、演化、生態）
- 海洋生物（深海、珊瑚礁、新物種）
- 神經科學（大腦、記憶、感知）
- 天文宇宙（行星、星系、太空任務）
- 醫療健康（新療法、研究突破）
- 科技趣聞（材料、工程、發明）

每張卡片輸出 JSON，格式如下（輸出純 JSON 陣列，不要加任何說明）：
[
  {{
    "id": "nature-{today_str[2:4]}{today_str[5:7]}a",
    "domain": "nature",
    "day": "{today_str}",
    "author": "Nature / 2026",
    "ref": "Nature 2026",
    "url": "https://www.nature.com/",
    "color": "#fbd38d",
    "title": {{
      "zh-TW": "繁體中文標題",
      "en": "English Title",
      "zh-CN": "简体中文标题",
      "ja": "日本語タイトル",
      "ko": "한국어 제목"
    }},
    "tag": {{
      "zh-TW": "🐠 自然生物",
      "en": "🐠 Nature & Wildlife",
      "zh-CN": "🐠 自然生物",
      "ja": "🐠 自然生物",
      "ko": "🐠 자연 생물"
    }},
    "tech": {{
      "zh-TW": "科學說明（2-3句）",
      "en": "Scientific explanation",
      "zh-CN": "科学说明",
      "ja": "科学的説明",
      "ko": "과학적 설명"
    }},
    "plain": {{
      "zh-TW": "白話解釋（有趣、生活化）",
      "en": "Fun plain explanation",
      "zh-CN": "白话解释",
      "ja": "わかりやすい説明",
      "ko": "쉬운 설명"
    }},
    "insight": {{
      "zh-TW": "💡 為什麼這很酷？",
      "en": "💡 Why it matters",
      "zh-CN": "💡 为什么值得关注",
      "ja": "💡 なぜ重要か",
      "ko": "💡 왜 중요한가"
    }}
  }}
]

重要：
- id 要唯一，6 張可加 a/b/c/d/e/f 後綴
- 每個領域用對應的 color
- url 盡量填真實文章連結
- 只輸出 JSON 陣列，不要有任何說明文字"""

    raw = call_claude(prompt, max_tokens=6000)

    json_match = re.search(r'\[[\s\S]*\]', raw)
    if not json_match:
        raise ValueError(f"API 回傳內容無法解析為 JSON:\n{raw[:500]}")

    cards = json.loads(json_match.group())
    log.info(f"生成 {len(cards)} 張週末趣知卡片")
    return cards


# ── 產生 SVG 插圖 ─────────────────────────────────────────────────────────
def generate_illus(card):
    domain = card.get("domain", "ai")
    cfg = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["ai"])
    emoji = cfg["emoji"]
    color = cfg["color"]
    label = cfg["label"]
    title_short = card["title"]["zh-TW"][:12]

    # 簡單 SVG，可之後由 gen_illustration.py 強化
    svg = f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}22" rx="12"/>
  <rect x="0" y="0" width="200" height="4" fill="{color}" rx="2"/>
  <text x="100" y="68" text-anchor="middle" font-size="44">{emoji}</text>
  <text x="16" y="20" font-size="10" fill="{color}" font-weight="bold">{label}</text>
  <text x="100" y="100" text-anchor="middle" font-size="9" fill="#555">{title_short}...</text>
</svg>'''
    return svg


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
def main():
    log.info("=" * 60)
    log.info("每日新知自動更新開始")

    date_info = get_date_info()
    log.info(f"今天：{date_info['today_str']} | 模式：{date_info['mode']} | paper_date：{date_info['paper_date_str']}")

    history = load_history()
    recent_topics = get_recent_topics(history)

    # 檢查今天是否已更新
    existing = [e for e in history["entries"] if e.get("date") == date_info["today_str"]]
    if existing:
        log.info(f"今天 {date_info['today_str']} 已更新過，跳過")
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
    main()
