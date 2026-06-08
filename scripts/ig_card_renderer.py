#!/usr/bin/env python3
"""
ig_card_renderer.py — 將知識卡片渲染成 1080×1080 PNG

流程：
  card dict → 自包含 HTML → Playwright 截圖 → Pillow 合成 1080×1080
"""

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent

# 品牌色
BRAND_TEAL  = "#4dbdb5"
BRAND_DARK  = "#0a2a28"

# 每個 domain 的顏色（與 index.html 一致）
DOMAIN_COLOR = {
    "ai":     "#2a9d8f",
    "bio":    "#52b788",
    "phys":   "#4a7bbf",
    "neuro":  "#6a1b9a",
    "health": "#b71c1c",
    "space":  "#1a237e",
    "chem":   "#bf5b9b",
    "tech":   "#00695c",
    "ocean":  "#01579b",
    "nature": "#2e7d32",
    "fin":    "#7dba3a",
    "arch":   "#e9a84c",
}

CARD_CSS = """
:root {
  --tf: #4dbdb5; --bg: #f0f4f3; --bg3: #e4eceb;
  --su: #ffffff; --bd: #dde6e5;
  --tx: #1a2e2c; --tx2: #3d5c59; --tx3: #7a9e9b;
  --sh: rgba(0,80,75,0.10);
  --accent: #4dbdb5; --fz: 1;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
               "Noto Sans TC", "Microsoft JhengHei", sans-serif;
  background: #f0f4f3;
  display: flex; align-items: center; justify-content: center;
  width: 900px; padding: 40px;
}
.card {
  background: #fff;
  border-radius: 22px;
  border: 1.5px solid #dde6e5;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,80,75,0.13);
  width: 820px;
  display: flex; flex-direction: column;
}
.stripe { height: 8px; }
.illus {
  width: 100%; max-height: 220px;
  overflow: hidden; display: flex;
  align-items: center; justify-content: center;
  background: #f7fbfa; padding: 12px 0 0;
}
.illus svg { width: 100%; max-height: 210px; }
.cbody { padding: 24px 30px 20px; display: flex; flex-direction: column; gap: 10px; }
.dtag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 13px; font-weight: 800; letter-spacing: 1px;
  text-transform: uppercase; padding: 4px 14px;
  border-radius: 10px; width: fit-content;
}
.card h2 {
  font-size: 22px; font-weight: 800; line-height: 1.5;
  color: #1a2e2c; margin: 4px 0;
}
.plain-label { font-size: 12px; font-weight: 700; color: #7a9e9b; letter-spacing: 0.5px; }
.intro {
  font-size: 15px; color: #3d5c59; line-height: 1.8;
  display: -webkit-box; -webkit-line-clamp: 4;
  -webkit-box-orient: vertical; overflow: hidden;
}
.insight {
  font-size: 14px; color: #3d5c59; line-height: 1.7;
  font-style: italic; padding: 10px 16px;
  background: #f0f4f3; border-radius: 10px;
  border-left: 4px solid #4dbdb5;
}
.cfoot {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 8px; border-top: 1px solid #dde6e5;
  font-size: 13px; color: #7a9e9b;
}
.ref { font-size: 12px; color: #7a9e9b; font-weight: 600; }
"""

def card_to_html(card: dict, lang: str = "zh-TW") -> str:
    """把一張 card dict 轉成自包含 HTML 字串"""
    def t(field):
        v = card.get(field, {})
        return v.get(lang) or v.get("zh-TW") or "" if isinstance(v, dict) else str(v)

    domain  = card.get("domain", "ai")
    color   = card.get("color") or DOMAIN_COLOR.get(domain, "#4dbdb5")
    illus   = card.get("illus", "")
    tag     = t("tag")
    title   = t("title")
    plain   = t("plain")
    insight = t("insight")
    ref     = card.get("ref", "")

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<style>{CARD_CSS}</style>
</head>
<body>
<div class="card" id="thecard">
  <div class="stripe" style="background:{color}"></div>
  <div class="illus">{illus}</div>
  <div class="cbody">
    <span class="dtag" style="color:{color};background:{color}22">{tag}</span>
    <h2>{title}</h2>
    <p class="plain-label">💬 白話解說</p>
    <p class="intro">{plain}</p>
    <div class="insight">{insight}</div>
    <div class="cfoot">
      <span class="ref">📄 {ref}</span>
      <span style="font-size:12px;font-weight:700;color:#4dbdb5">每日新知</span>
    </div>
  </div>
</div>
</body>
</html>"""


def render_card_png(card: dict, lang: str = "zh-TW") -> bytes:
    """
    回傳 1080×1080 PNG bytes（可直接上傳 Instagram）
    """
    from playwright.sync_api import sync_playwright

    html = card_to_html(card, lang)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 980, "height": 1400})
        page.set_content(html, wait_until="networkidle")

        # 截圖卡片元素
        el = page.locator("#thecard")
        card_png = el.screenshot(type="png")
        browser.close()

    # ── Pillow：貼到 1080×1080 canvas ──
    card_img = Image.open(io.BytesIO(card_png)).convert("RGBA")
    cw, ch = card_img.size

    canvas_size = 1080
    # 計算縮放：卡片最多佔 canvas 的 88%
    max_card_w = int(canvas_size * 0.88)
    if cw > max_card_w:
        scale = max_card_w / cw
        card_img = card_img.resize((int(cw * scale), int(ch * scale)), Image.LANCZOS)
        cw, ch = card_img.size

    # 背景：品牌漸層感（淺綠）
    canvas = Image.new("RGBA", (canvas_size, canvas_size), "#eaf4f3")
    draw = ImageDraw.Draw(canvas)

    # 底部品牌色條（高度 72px）
    bar_h = 72
    draw.rectangle([(0, canvas_size - bar_h), (canvas_size, canvas_size)],
                   fill=BRAND_TEAL)

    # 品牌文字（底部色條內）
    try:
        font_path = "C:/Windows/Fonts/msjh.ttc"  # 微軟正黑體
        font_brand = ImageFont.truetype(font_path, 24)
        font_url   = ImageFont.truetype(font_path, 20)
    except Exception:
        font_brand = ImageFont.load_default()
        font_url   = font_brand

    brand_text = "每日新知  Daily Knowledge"
    url_text   = "k6306woody.github.io/DailyKnowledge"
    draw.text((canvas_size // 2, canvas_size - bar_h + 18),
              brand_text, fill="white", font=font_brand, anchor="mt")
    draw.text((canvas_size // 2, canvas_size - bar_h + 46),
              url_text, fill="#c8efec", font=font_url, anchor="mt")

    # 卡片置中（垂直方向偏上一點，留出底部色條空間）
    usable_h = canvas_size - bar_h - 20
    paste_x = (canvas_size - cw) // 2
    paste_y = max(16, (usable_h - ch) // 2)

    canvas.paste(card_img, (paste_x, paste_y), mask=card_img)

    # 輸出 PNG bytes
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def save_card_png(card: dict, out_path: Path, lang: str = "zh-TW") -> Path:
    """render_card_png 的便利包裝，直接存檔"""
    png_bytes = render_card_png(card, lang)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png_bytes)
    return out_path


# ── CLI 測試 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, json
    sys.stdout = __import__("io").TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

    # 讀最新一天的 JSON 做測試
    data_dir = ROOT / "data"
    jsons = sorted(data_dir.glob("*.json"), reverse=True)
    if not jsons:
        print("找不到 data/*.json")
        sys.exit(1)

    with open(jsons[0], encoding="utf-8") as f:
        data = json.load(f)

    card = data["cards"][0]
    out = ROOT / "ig_tmp" / f"test_{data['date']}.png"
    print(f"渲染卡片：{card['id']} → {out}")
    save_card_png(card, out)
    print(f"✅ 完成！PNG 大小：{out.stat().st_size // 1024} KB")
    print(f"   檔案：{out}")
