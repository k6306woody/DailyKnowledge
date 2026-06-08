#!/usr/bin/env python3
"""
ig_poster.py — Instagram Graph API 自動發文

功能：
  - 將知識卡片圖片發布到 Instagram Business 帳號
  - 自動管理 60-day Long-lived Token（7天前自動刷新）
  - Token meta 存於 ROOT/.ig_token_meta.json（已加入 .gitignore）

使用前提：
  .env 需包含：
    IG_ACCESS_TOKEN=EAAxxxxxxxx
    IG_BUSINESS_ID=1234567890
    IG_APP_ID=xxxxxxxxxx        （刷新 token 用）
    IG_APP_SECRET=xxxxxxxxxx    （刷新 token 用）

執行：
  python scripts/ig_poster.py              # 發今天最新卡片
  python scripts/ig_poster.py --test       # 只產圖，不真正發文
  python scripts/ig_poster.py --card-index 2  # 發第3張卡（0-based）
"""

import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

TOKEN_META_FILE = ROOT / ".ig_token_meta.json"
IG_TMP_DIR      = ROOT / "ig_tmp"
GRAPH_BASE      = "https://graph.facebook.com/v21.0"

log = logging.getLogger("ig_poster")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "logs" / "ig_post.log",
                            encoding="utf-8", errors="replace"),
    ]
)


# ── Token 管理 ────────────────────────────────────────────────────────────

def load_token_meta() -> dict:
    if TOKEN_META_FILE.exists():
        with open(TOKEN_META_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_token_meta(meta: dict):
    with open(TOKEN_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def get_valid_token() -> str:
    """取得有效 token，若距到期 ≤ 7 天則自動刷新"""
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("IG_ACCESS_TOKEN 未設定")

    meta = load_token_meta()
    expires_str = meta.get("expires")

    if expires_str:
        expires = datetime.fromisoformat(expires_str)
        days_left = (expires - datetime.now()).days
        log.info(f"Token 剩餘有效天數：{days_left} 天")
        if days_left > 7:
            return token
        log.info("Token 接近到期，嘗試刷新...")

    # 刷新 token
    app_id     = os.environ.get("IG_APP_ID", "")
    app_secret = os.environ.get("IG_APP_SECRET", "")
    if not app_id or not app_secret:
        log.warning("IG_APP_ID / IG_APP_SECRET 未設定，無法刷新 token，使用現有 token")
        return token

    resp = requests.get(
        "https://graph.facebook.com/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         app_id,
            "client_secret":     app_secret,
            "fb_exchange_token": token,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    new_token = data.get("access_token", "")
    expires_in = data.get("expires_in", 60 * 24 * 3600)  # 預設 60 天

    if new_token:
        new_expires = datetime.now() + timedelta(seconds=expires_in)
        save_token_meta({"expires": new_expires.isoformat(), "refreshed_at": datetime.now().isoformat()})

        # 更新 .env 中的 token
        env_path = ROOT / ".env"
        env_text = env_path.read_text(encoding="utf-8")
        lines = []
        updated = False
        for line in env_text.splitlines():
            if line.startswith("IG_ACCESS_TOKEN="):
                lines.append(f"IG_ACCESS_TOKEN={new_token}")
                updated = True
            else:
                lines.append(line)
        if not updated:
            lines.append(f"IG_ACCESS_TOKEN={new_token}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        log.info(f"✅ Token 刷新成功，新到期日：{new_expires.strftime('%Y-%m-%d')}")
        return new_token

    log.warning("Token 刷新回應無效，使用舊 token")
    return token


# ── 圖片上傳（透過 GitHub raw URL）───────────────────────────────────────

def push_image_to_github(png_path: Path, date_str: str) -> str:
    """
    把 PNG 推到 GitHub repo，回傳 raw URL。
    使用 git 命令（repo 已設定好 origin）。
    """
    import subprocess

    rel_path = png_path.relative_to(ROOT)

    def run(cmd):
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    run(["git", "add", str(rel_path)])
    status = run(["git", "status", "--porcelain"])
    if status:
        run(["git", "commit", "-m", f"ig: add card image {date_str}"])
        run(["git", "push"])
        log.info(f"  圖片已推到 GitHub：{rel_path}")
        # GitHub raw URL 有時需要 30-90 秒才能生效
        log.info("  等待 60 秒讓 GitHub raw content 生效...")
        time.sleep(60)
    else:
        log.info("  圖片已存在（無變更），跳過 push")

    # 取得 remote URL，拼出 raw URL
    remote = run(["git", "remote", "get-url", "origin"])
    # e.g. https://github.com/k6306woody/DailyKnowledge.git
    repo_path = remote.replace("https://github.com/", "").rstrip(".git")
    raw_url = f"https://raw.githubusercontent.com/{repo_path}/main/{rel_path.as_posix()}"
    return raw_url


# ── Instagram Graph API ───────────────────────────────────────────────────

def create_media_container(token: str, ig_id: str, image_url: str, caption: str) -> str:
    """建立 media container，回傳 creation_id"""
    resp = requests.post(
        f"{GRAPH_BASE}/{ig_id}/media",
        params={"access_token": token},
        json={
            "image_url": image_url,
            "caption":   caption,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    creation_id = data.get("id")
    if not creation_id:
        raise RuntimeError(f"建立 container 失敗：{data}")
    log.info(f"  Media container 建立：{creation_id}")
    return creation_id


def publish_container(token: str, ig_id: str, creation_id: str) -> str:
    """發布 container，回傳 media_id"""
    resp = requests.post(
        f"{GRAPH_BASE}/{ig_id}/media_publish",
        params={"access_token": token},
        json={"creation_id": creation_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    media_id = data.get("id")
    if not media_id:
        raise RuntimeError(f"發布失敗：{data}")
    log.info(f"  ✅ 發布成功！media_id={media_id}")
    return media_id


def build_caption(card: dict) -> str:
    """組成 Instagram caption（繁體中文 + hashtag）"""
    def t(field):
        v = card.get(field, {})
        return v.get("zh-TW") or v.get("en") or "" if isinstance(v, dict) else str(v)

    domain  = card.get("domain", "ai")
    title   = t("title")
    plain   = t("plain")
    insight = t("insight").replace("💡 ", "")
    ref     = card.get("ref", "")

    # 截短 plain 到 150 字
    plain_short = plain[:150] + "…" if len(plain) > 150 else plain

    # domain 對應的 hashtag（英文）
    domain_tags = {
        "ai": "#AI #人工智慧 #MachineLearning",
        "bio": "#生命科學 #Biology #Genomics",
        "phys": "#物理 #Physics #QuantumPhysics",
        "neuro": "#神經科學 #Neuroscience #Brain",
        "health": "#健康科學 #Health #Medicine",
        "space": "#天文 #Astronomy #Space",
        "chem": "#化學 #Chemistry #Materials",
        "tech": "#科技 #Technology #Engineering",
        "ocean": "#海洋科學 #OceanScience",
        "nature": "#自然科學 #Nature #Ecology",
        "fin": "#財經 #Finance #Economics",
        "arch": "#建築 #Architecture #Design",
    }
    extra_tags = domain_tags.get(domain, f"#{domain}")

    caption = f"""{title}

{plain_short}

💡 {insight[:100]}

📖 {ref}
🔗 每日新知：k6306woody.github.io/DailyKnowledge

#每日新知 #DailyKnowledge #科普 #學術研究 #知識 #arXiv {extra_tags} #台灣 #繁體中文"""

    return caption[:2200]  # IG caption 上限


# ── 主要對外函式 ──────────────────────────────────────────────────────────

def post_daily_card(card: dict, date_str: str, test_mode: bool = False) -> bool:
    """
    把一張卡片渲染成 PNG 並發布到 Instagram。
    test_mode=True 只產圖不發文，用於測試。
    回傳 True 表示成功。
    """
    from scripts.ig_card_renderer import save_card_png  # 避免循環 import

    ig_id = os.environ.get("IG_BUSINESS_ID", "")
    if not ig_id and not test_mode:
        log.warning("IG_BUSINESS_ID 未設定，跳過 Instagram 發文")
        return False

    log.info(f"── Instagram 發文：{card['id']} ({date_str}) ──")

    # 1. 渲染 PNG
    IG_TMP_DIR.mkdir(exist_ok=True)
    png_path = IG_TMP_DIR / f"{date_str}.png"
    log.info(f"  渲染卡片圖片：{png_path.name}")
    save_card_png(card, png_path)
    log.info(f"  PNG 大小：{png_path.stat().st_size // 1024} KB")

    if test_mode:
        log.info(f"  [TEST MODE] 圖片已儲存，不發文：{png_path}")
        return True

    # 2. Push 圖片到 GitHub，取得 raw URL
    log.info("  上傳圖片到 GitHub...")
    image_url = push_image_to_github(png_path, date_str)
    log.info(f"  圖片 URL：{image_url}")

    # 3. 取得有效 token
    token = get_valid_token()

    # 4. 組 caption
    caption = build_caption(card)
    log.info(f"  Caption（前100字）：{caption[:100]}...")

    # 5. 建立 container
    creation_id = create_media_container(token, ig_id, image_url, caption)

    # 6. 等待 container 處理（Instagram 建議等 5-10 秒）
    log.info("  等待 container 處理（10秒）...")
    time.sleep(10)

    # 7. 發布
    publish_container(token, ig_id, creation_id)
    return True


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Instagram 自動發文")
    parser.add_argument("--test", action="store_true", help="只產圖，不發文")
    parser.add_argument("--date", default=None, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--card-index", type=int, default=0, help="發第幾張卡（0-based）")
    args = parser.parse_args()

    # 讀取卡片資料
    data_dir = ROOT / "data"
    if args.date:
        json_path = data_dir / f"{args.date}.json"
    else:
        jsons = sorted(data_dir.glob("*.json"), reverse=True)
        if not jsons:
            log.error("找不到任何 JSON 資料")
            sys.exit(1)
        json_path = jsons[0]

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    cards = data.get("cards", [])
    if not cards:
        log.error(f"JSON 中沒有卡片：{json_path}")
        sys.exit(1)

    idx = min(args.card_index, len(cards) - 1)
    card = cards[idx]
    date_str = data["date"]

    log.info(f"選用卡片 [{idx}]：{card['id']} — {card.get('title', {}).get('zh-TW', '')[:40]}")
    success = post_daily_card(card, date_str, test_mode=args.test)
    sys.exit(0 if success else 1)
