#!/usr/bin/env python3
"""
fix_splash_transition.py
把 Splash 轉場改成：放大淡出（zoom + fade）→ 主畫面純淡入
不再有「往上滑走」的效果，與粒子動畫更協調。
"""
import re
from pathlib import Path

TARGET = Path(__file__).parent.parent / "index.html"
html = TARGET.read_text(encoding='utf-8')
original = html

# ── 1. splashOut：改成放大淡出 ──
# 不管現在是哪個版本，用 regex 整批替換
html = re.sub(
    r'@keyframes splashOut\{[^}]*\}',
    '@keyframes splashOut{0%{opacity:1;transform:scale(1)}40%{opacity:1;transform:scale(1.04)}100%{opacity:0;transform:scale(1.1)}}',
    html
)
# 多行版本也處理
html = re.sub(
    r'@keyframes splashOut\{[\s\S]*?\}\s*\}',
    '@keyframes splashOut{0%{opacity:1;transform:scale(1)}40%{opacity:1;transform:scale(1.04)}100%{opacity:0;transform:scale(1.1)}}',
    html,
    count=1
)

# ── 2. splash animation 時間：0.9s cubic-bezier，delay 2.5s ──
html = re.sub(
    r'animation:splashOut [^;]+;',
    'animation:splashOut .9s cubic-bezier(.4,0,.6,1) 2.5s forwards;',
    html
)

# ── 3. will-change 補充 opacity ──
html = html.replace('will-change:transform;', 'will-change:transform,opacity;')

# ── 4. appIn：純淡入，不帶 translateY ──
html = re.sub(
    r'@keyframes appIn\{[^}]*\}',
    '@keyframes appIn{from{opacity:0}to{opacity:1}}',
    html
)

# ── 5. #app animation timing：配合 splash 結束時間（2.5+0.9=3.4s 完成，app 從 3.0s 開始） ──
html = re.sub(
    r'(#app\{animation:appIn )[^;]+;',
    r'\g<1>.8s ease-out 3.0s both;',
    html
)

# ── 驗證 & 存檔 ──
checks = [
    ('scale(1.1)', '放大淡出 keyframe'),
    ('cubic-bezier(.4,0,.6,1)', 'splash timing'),
    ('from{opacity:0}to{opacity:1}', 'appIn 純淡入'),
]
print("驗證：")
all_ok = True
for snippet, label in checks:
    ok = snippet in html
    print(f"  {'✅' if ok else '❌'} {label}")
    if not ok: all_ok = False

if html != original:
    TARGET.write_text(html, encoding='utf-8')
    print(f"\n✅ 已儲存 {TARGET} ({TARGET.stat().st_size//1024}KB)")
else:
    print("\n⚠️  內容未變動，請檢查是否已是最新版")
