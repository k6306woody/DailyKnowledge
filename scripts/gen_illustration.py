#!/usr/bin/env python3
"""
gen_illustration.py — 每日新知 SVG 插圖生成器
每個 domain 一套精美 200x120 的圖形，供 daily_update.py 呼叫
介面：generate_illus(card: dict) -> str  回傳 SVG 字串
"""


def generate_illus(card: dict) -> str:
    """根據 card 的 domain 回傳對應的 SVG 插圖字串"""
    domain = card.get("domain", "ai")
    color = card.get("color", "#667eea")
    generator = DOMAIN_GENERATORS.get(domain, _fallback)
    return generator(color)


# ─────────────────────────────────────────────
# 各 domain 插圖函式
# ─────────────────────────────────────────────

def _ai(color="#667eea"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <line x1="30" y1="42" x2="80" y2="42" stroke="{color}" stroke-width="1.2" opacity=".5"/>
  <line x1="80" y1="42" x2="80" y2="70" stroke="{color}" stroke-width="1.2" opacity=".5"/>
  <line x1="80" y1="70" x2="166" y2="70" stroke="{color}" stroke-width="1.2" opacity=".5"/>
  <line x1="120" y1="42" x2="120" y2="56" stroke="{color}" stroke-width="1.2" opacity=".5"/>
  <line x1="100" y1="56" x2="166" y2="56" stroke="{color}" stroke-width="1.2" opacity=".5"/>
  <circle cx="80" cy="42" r="5" fill="{color}"/>
  <circle cx="120" cy="42" r="5" fill="{color}"/>
  <circle cx="80" cy="70" r="5" fill="{color}"/>
  <circle cx="140" cy="70" r="5" fill="{color}" opacity=".6"/>
  <circle cx="140" cy="56" r="5" fill="{color}" opacity=".6"/>
  <rect x="90" y="49" width="20" height="20" rx="2" fill="{color}"/>
  <rect x="93" y="52" width="14" height="14" rx="1" fill="{color}18"/>
  <text x="100" y="63" text-anchor="middle" font-size="8" fill="white" font-weight="700" font-family="sans-serif">AI</text>
  <circle cx="30" cy="42" r="3" fill="{color}" opacity=".4"/>
  <circle cx="166" cy="56" r="3" fill="{color}" opacity=".4"/>
  <circle cx="166" cy="70" r="3" fill="{color}" opacity=".4"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🤖 人工智慧</text>
</svg>'''


def _bio(color="#48bb78"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <path d="M60 22 C75 34 85 34 100 22 C115 10 125 10 140 22 C155 34 165 34 140 46 C125 58 115 58 100 46 C85 34 75 34 60 46 C45 58 35 58 60 70 C75 82 85 82 100 70 C115 58 125 58 140 70 C155 82 165 82 140 94" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".7"/>
  <path d="M60 22 C45 34 35 34 60 46 C75 58 85 58 100 46 C115 34 125 34 140 22" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" opacity=".5"/>
  <line x1="70" y1="28" x2="90" y2="28" stroke="{color}" stroke-width="1.5" opacity=".6"/>
  <line x1="108" y1="40" x2="128" y2="40" stroke="{color}" stroke-width="1.5" opacity=".6"/>
  <line x1="68" y1="60" x2="88" y2="60" stroke="{color}" stroke-width="1.5" opacity=".6"/>
  <line x1="110" y1="74" x2="130" y2="74" stroke="{color}" stroke-width="1.5" opacity=".6"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🧬 生命科學</text>
</svg>'''


def _phys(color="#ed8936"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <ellipse cx="100" cy="64" rx="42" ry="17" fill="none" stroke="{color}" stroke-width="1.5" opacity=".7"/>
  <ellipse cx="100" cy="64" rx="42" ry="17" fill="none" stroke="{color}" stroke-width="1.5" opacity=".7" transform="rotate(60 100 64)"/>
  <ellipse cx="100" cy="64" rx="42" ry="17" fill="none" stroke="{color}" stroke-width="1.5" opacity=".7" transform="rotate(120 100 64)"/>
  <circle cx="100" cy="64" r="8" fill="{color}"/>
  <circle cx="142" cy="64" r="4" fill="{color}cc"/>
  <circle cx="77" cy="47" r="4" fill="{color}cc"/>
  <circle cx="77" cy="81" r="4" fill="{color}cc"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">⚛️ 物理科學</text>
</svg>'''


def _neuro(color="#9f7aea"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <circle cx="38" cy="48" r="6" fill="{color}" opacity=".5"/>
  <circle cx="38" cy="68" r="6" fill="{color}" opacity=".5"/>
  <circle cx="38" cy="88" r="6" fill="{color}" opacity=".5"/>
  <circle cx="100" cy="38" r="6" fill="{color}" opacity=".7"/>
  <circle cx="100" cy="58" r="6" fill="{color}" opacity=".7"/>
  <circle cx="100" cy="78" r="6" fill="{color}" opacity=".7"/>
  <circle cx="100" cy="98" r="6" fill="{color}" opacity=".7"/>
  <circle cx="158" cy="53" r="9" fill="{color}"/>
  <circle cx="158" cy="83" r="9" fill="{color}"/>
  <line x1="44" y1="48" x2="94" y2="38" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="44" y1="48" x2="94" y2="58" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="44" y1="68" x2="94" y2="58" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="44" y1="68" x2="94" y2="78" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="44" y1="88" x2="94" y2="78" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="44" y1="88" x2="94" y2="98" stroke="{color}" stroke-width="0.8" opacity=".4"/>
  <line x1="106" y1="38" x2="149" y2="53" stroke="{color}" stroke-width="1" opacity=".5"/>
  <line x1="106" y1="58" x2="149" y2="53" stroke="{color}" stroke-width="1" opacity=".5"/>
  <line x1="106" y1="78" x2="149" y2="83" stroke="{color}" stroke-width="1" opacity=".5"/>
  <line x1="106" y1="98" x2="149" y2="83" stroke="{color}" stroke-width="1" opacity=".5"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🧠 神經科學</text>
</svg>'''


def _health(color="#fc8181"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <polyline points="16,65 42,65 52,35 62,92 72,50 82,65 108,65 128,65 142,65 172,65"
            fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="148" y="22" width="8" height="24" rx="2" fill="{color}" opacity=".5"/>
  <rect x="140" y="30" width="24" height="8" rx="2" fill="{color}" opacity=".5"/>
  <circle cx="62" cy="92" r="4" fill="{color}"/>
  <circle cx="72" cy="50" r="4" fill="{color}"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🏥 醫療健康</text>
</svg>'''


def _space(color="#4299e1"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <circle cx="30" cy="32" r="1.5" fill="{color}" opacity=".7"/>
  <circle cx="55" cy="22" r="1" fill="{color}" opacity=".6"/>
  <circle cx="162" cy="27" r="1.5" fill="{color}" opacity=".7"/>
  <circle cx="178" cy="48" r="1" fill="{color}" opacity=".5"/>
  <circle cx="142" cy="17" r="2" fill="{color}" opacity=".8"/>
  <circle cx="22" cy="57" r="1" fill="{color}" opacity=".5"/>
  <circle cx="100" cy="65" r="30" fill="{color}" opacity=".15"/>
  <circle cx="100" cy="65" r="21" fill="{color}" opacity=".35"/>
  <circle cx="100" cy="65" r="13" fill="{color}"/>
  <ellipse cx="100" cy="65" rx="38" ry="10" fill="none" stroke="{color}" stroke-width="2" opacity=".4"/>
  <circle cx="148" cy="40" r="8" fill="{color}55"/>
  <circle cx="148" cy="40" r="5" fill="{color}88"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🌌 天文宇宙</text>
</svg>'''


def _chem(color="#d4a600"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <polygon points="100,26 124,39 124,66 100,79 76,66 76,39"
           fill="none" stroke="{color}" stroke-width="2" opacity=".6"/>
  <polygon points="100,34 116,44 116,61 100,71 84,61 84,44"
           fill="none" stroke="{color}" stroke-width="1.2" opacity=".35"/>
  <circle cx="100" cy="26" r="5" fill="{color}"/>
  <circle cx="124" cy="39" r="5" fill="{color}" opacity=".8"/>
  <circle cx="124" cy="66" r="5" fill="{color}" opacity=".8"/>
  <circle cx="100" cy="79" r="5" fill="{color}"/>
  <circle cx="76" cy="66" r="5" fill="{color}" opacity=".8"/>
  <circle cx="76" cy="39" r="5" fill="{color}" opacity=".8"/>
  <path d="M150 30 L150 58 L164 83 L136 83 Z"
        fill="{color}22" stroke="{color}" stroke-width="1.5"/>
  <line x1="144" y1="44" x2="156" y2="44" stroke="{color}" stroke-width="1"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🧪 化學材料</text>
</svg>'''


def _tech(color="#38a169"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <circle cx="100" cy="88" r="4" fill="{color}"/>
  <path d="M80 73 Q100 53 120 73" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".5"/>
  <path d="M62 57 Q100 27 138 57" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".4"/>
  <path d="M44 41 Q100 1 156 41" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".3"/>
  <rect x="18" y="72" width="30" height="22" rx="3" fill="{color}30" stroke="{color}" stroke-width="1"/>
  <rect x="152" y="72" width="30" height="22" rx="3" fill="{color}30" stroke="{color}" stroke-width="1"/>
  <line x1="48" y1="83" x2="80" y2="88" stroke="{color}" stroke-width="1" opacity=".4" stroke-dasharray="3,2"/>
  <line x1="120" y1="88" x2="152" y2="83" stroke="{color}" stroke-width="1" opacity=".4" stroke-dasharray="3,2"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">📶 科技趣聞</text>
</svg>'''


def _ocean(color="#38b2ac"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <path d="M0 75 Q25 63 50 75 Q75 87 100 75 Q125 63 150 75 Q175 87 200 75"
        fill="none" stroke="{color}" stroke-width="1.5" opacity=".5"/>
  <path d="M0 88 Q25 76 50 88 Q75 100 100 88 Q125 76 150 88 Q175 100 200 88"
        fill="none" stroke="{color}" stroke-width="1.5" opacity=".3"/>
  <path d="M38 62 Q70 37 112 57 Q132 62 122 72 Q92 82 48 72 Z"
        fill="{color}" opacity=".45"/>
  <path d="M90 40 L98 57 L82 52 Z" fill="{color}" opacity=".7"/>
  <circle cx="97" cy="60" r="2" fill="white" opacity=".8"/>
  <circle cx="142" cy="47" r="4" fill="none" stroke="{color}" stroke-width="1" opacity=".5"/>
  <circle cx="154" cy="37" r="2.5" fill="none" stroke="{color}" stroke-width="1" opacity=".4"/>
  <circle cx="162" cy="52" r="3" fill="none" stroke="{color}" stroke-width="1" opacity=".4"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🦈 海洋生物</text>
</svg>'''


def _nature(color="#d97706"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <rect x="95" y="78" width="8" height="24" fill="{color}" opacity=".5"/>
  <ellipse cx="99" cy="60" rx="30" ry="25" fill="{color}" opacity=".25"/>
  <ellipse cx="80" cy="55" rx="20" ry="17" fill="{color}" opacity=".35"/>
  <ellipse cx="118" cy="55" rx="20" ry="17" fill="{color}" opacity=".35"/>
  <ellipse cx="99" cy="38" rx="22" ry="19" fill="{color}" opacity=".5"/>
  <circle cx="162" cy="28" r="13" fill="{color}" opacity=".2"/>
  <circle cx="162" cy="28" r="8" fill="{color}" opacity=".5"/>
  <path d="M28 37 Q38 30 48 37" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" opacity=".6"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🐠 自然生物</text>
</svg>'''


def _fin(color="#d53f8c"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <line x1="18" y1="102" x2="180" y2="102" stroke="{color}" stroke-width="0.8" opacity=".3"/>
  <rect x="28" y="76" width="20" height="26" rx="2" fill="{color}" opacity=".35"/>
  <rect x="56" y="56" width="20" height="46" rx="2" fill="{color}" opacity=".45"/>
  <rect x="84" y="40" width="20" height="62" rx="2" fill="{color}" opacity=".55"/>
  <rect x="112" y="24" width="20" height="78" rx="2" fill="{color}" opacity=".65"/>
  <rect x="140" y="34" width="20" height="68" rx="2" fill="{color}" opacity=".75"/>
  <polyline points="38,76 66,56 94,42 122,26 150,36"
            fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <circle cx="150" cy="36" r="4" fill="{color}"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">💰 經濟金融</text>
</svg>'''


def _arch(color="#718096"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <rect x="52" y="96" width="96" height="6" rx="1" fill="{color}" opacity=".5"/>
  <rect x="60" y="46" width="10" height="50" rx="1" fill="{color}" opacity=".4"/>
  <rect x="78" y="46" width="10" height="50" rx="1" fill="{color}" opacity=".4"/>
  <rect x="96" y="46" width="10" height="50" rx="1" fill="{color}" opacity=".4"/>
  <rect x="114" y="46" width="10" height="50" rx="1" fill="{color}" opacity=".4"/>
  <rect x="130" y="46" width="10" height="50" rx="1" fill="{color}" opacity=".4"/>
  <rect x="50" y="38" width="100" height="9" rx="1" fill="{color}" opacity=".6"/>
  <polygon points="100,14 150,38 50,38" fill="none" stroke="{color}" stroke-width="1.5" opacity=".5"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">🏛️ 建築環境</text>
</svg>'''


def _fallback(color="#a0aec0"):
    return f'''<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="{color}18" rx="10"/>
  <rect width="200" height="4" rx="2" fill="{color}"/>
  <circle cx="100" cy="62" r="28" fill="none" stroke="{color}" stroke-width="2" opacity=".4"/>
  <circle cx="100" cy="62" r="16" fill="{color}" opacity=".3"/>
  <circle cx="100" cy="62" r="6" fill="{color}"/>
  <text x="10" y="113" font-size="9" fill="{color}" font-weight="600" font-family="sans-serif">📌 知識</text>
</svg>'''


# ── 對應表 ────────────────────────────────────────────────────────────────
DOMAIN_GENERATORS = {
    "ai":     _ai,
    "bio":    _bio,
    "phys":   _phys,
    "neuro":  _neuro,
    "health": _health,
    "space":  _space,
    "chem":   _chem,
    "tech":   _tech,
    "ocean":  _ocean,
    "nature": _nature,
    "fin":    _fin,
    "arch":   _arch,
    # aliases
    "robot":  _ai,
    "climate": _nature,
}


# ── 測試 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for domain, gen in DOMAIN_GENERATORS.items():
        svg = gen()
        print(f"{domain}: {len(svg)} chars OK")
    print("✅ 全部 domain 插圖生成正常")
