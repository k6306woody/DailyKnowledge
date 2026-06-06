#!/usr/bin/env python3
"""
copy_html_once.py — 一次性腳本
把 Cowork 輸出的 daily-knowledge-v4.html 複製到專案資料夾，改名為 index.html
執行完就可以刪掉這個腳本。
"""

import shutil
import glob
from pathlib import Path

DST = Path(r"D:\AI\Claude_agent\daily-knowledge\index.html")

# 在 Cowork session 資料夾中搜尋
SESSION_BASE = Path(r"C:\Users\User\AppData\Roaming\Claude\local-agent-mode-sessions")
candidates = list(SESSION_BASE.rglob("outputs/daily-knowledge-v4.html"))

if not candidates:
    # 備選：直接讓使用者輸入路徑
    print("找不到 daily-knowledge-v4.html，請手動複製：")
    print(f"  從：C:\\Users\\User\\AppData\\Roaming\\Claude\\...\\outputs\\daily-knowledge-v4.html")
    print(f"  到：{DST}")
else:
    # 選最新修改的那個
    src = max(candidates, key=lambda p: p.stat().st_mtime)
    print(f"找到：{src}")
    shutil.copy2(src, DST)
    print(f"✅ 複製完成：{DST}")
    print(f"   大小：{DST.stat().st_size // 1024} KB")
