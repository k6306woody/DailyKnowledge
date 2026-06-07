"""
enrich_plain.py
─────────────────────────────────────────────────
把 data/*.json 裡每張卡的 plain 欄位（5 種語言）
重新呼叫 Claude API 生成更豐富的「大白話說明」。

原始 plain 約 1-2 句；目標：5-8 句（250~400 字中文）
包含：類比、舉例、生活化連結、為什麼重要。

執行方式：
  python scripts/enrich_plain.py              # 處理所有 JSON
  python scripts/enrich_plain.py 2026-06-08   # 只處理特定日期
"""

import os, sys, json, time, io
from pathlib import Path
import anthropic

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DATA_DIR = Path(__file__).parent.parent / "data"
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

LANGS = ["zh-TW", "en", "zh-CN", "ja", "ko"]

SYSTEM_PROMPT = """你是一位擅長科普寫作的作家，專門把學術論文用生動的白話文說明給一般人聽。
你的說明需要：
- 用貼近生活的類比或故事開頭
- 解釋「為什麼這很重要？對我的生活有什麼影響？」
- 舉出 1-2 個具體例子或情境
- 語氣輕鬆、有趣，但不失準確性
- 長度：5-8 句話（不要用條列，連貫段落）
"""

LANG_INST = {
    "zh-TW": "請用繁體中文寫",
    "en":    "Write in English",
    "zh-CN": "请用简体中文写",
    "ja":    "日本語で書いてください",
    "ko":    "한국어로 작성해 주세요",
}

def enrich_card_plain(card: dict) -> dict:
    """呼叫 API 為一張卡生成新的 5 語言 plain"""
    domain = card.get("domain", "")
    # 用 zh-TW 的 title/tech 作為上下文（最完整）
    title = card.get("title", {})
    tech  = card.get("tech",  {})
    title_zh = title.get("zh-TW", "") if isinstance(title, dict) else str(title)
    tech_zh  = tech.get("zh-TW", "")  if isinstance(tech,  dict) else str(tech)
    old_plain = card.get("plain", {})
    if isinstance(old_plain, dict):
        old_plain_zh = old_plain.get("zh-TW", "")
    else:
        old_plain_zh = str(old_plain)

    new_plains = {}
    for lang in LANGS:
        inst = LANG_INST[lang]
        prompt = f"""{inst}，幫我把以下學術論文的摘要改寫成豐富的大白話說明。

論文標題（繁中）：{title_zh}
研究內容（繁中）：{tech_zh}
原本的白話說明（繁中，較短）：{old_plain_zh}

請生成一段 5-8 句話的白話說明，要有類比、舉例、為什麼重要，語氣輕鬆。
只回傳說明段落本身，不要任何標題或多餘格式。"""

        try:
            msg = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            new_plains[lang] = msg.content[0].text.strip()
            print(f"    [{lang}] ✓ {new_plains[lang][:60]}…")
        except Exception as e:
            print(f"    [{lang}] ✗ Error: {e} — keeping original")
            new_plains[lang] = old_plain.get(lang, old_plain_zh) if isinstance(old_plain, dict) else old_plain_zh
        time.sleep(0.5)  # 避免 rate limit

    return new_plains


def process_file(json_path: Path):
    print(f"\n{'='*55}")
    print(f"處理：{json_path.name}")
    print(f"{'='*55}")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    cards = data.get("cards", [])
    changed = False
    for i, card in enumerate(cards):
        cid = card.get("id", f"card-{i}")
        title_str = ""
        t = card.get("title", {})
        if isinstance(t, dict):
            title_str = t.get("zh-TW", "")[:40]
        else:
            title_str = str(t)[:40]
        print(f"\n  卡片 {i+1}/{len(cards)}: {cid} — {title_str}")
        new_plains = enrich_card_plain(card)
        card["plain"] = new_plains
        changed = True

    if changed:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ 已寫回 {json_path.name}")


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]  # e.g. "2026-06-08"
        path = DATA_DIR / f"{target}.json"
        if not path.exists():
            print(f"找不到 {path}")
            sys.exit(1)
        process_file(path)
    else:
        json_files = sorted(DATA_DIR.glob("*.json"))
        print(f"找到 {len(json_files)} 個 JSON 檔案")
        for p in json_files:
            process_file(p)

    print("\n\n🎉 全部完成！")

if __name__ == "__main__":
    main()
