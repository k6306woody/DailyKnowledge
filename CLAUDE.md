# 每日新知 (Daily Knowledge) — Claude Code 專案說明

> 進入專案後請先完整讀完此文件，再開始任何工作。

---

## 一、專案概述

每天凌晨 3am 自動更新知識卡片網站，並可發布到 Instagram：
- **平日（週一～週五）**：最新 arXiv 學術論文，白話解說
- **假日（週六～週日）**：科學趣知、世界新發現

5 種語言：繁體中文 / English / 简体中文 / 日本語 / 한국어

---

## 二、目錄結構

```
D:\AI\Claude_agent\daily-knowledge\
├── CLAUDE.md                ← 你現在讀的這份
├── index.html               ← 主網頁模板（頁面載入時 fetch JSON）
├── data\
│   └── YYYY-MM-DD.json      ← 每天一個資料檔（約 8KB）
├── history.json             ← 已發布主題（防重複用）
├── scripts\
│   ├── daily_update.py      ← 每天 3am 自動執行 ✅ 已完成
│   ├── setup_scheduler.py   ← 設定 Windows 排程 ✅ 已完成
│   ├── copy_html_once.py    ← 一次性複製 HTML（完成後可刪）
│   ├── gen_illustration.py  ← SVG 插圖生成 ❌ 尚未建立
│   └── post_instagram.py    ← IG 發文 ❌ 尚未建立（等 token）
├── logs\                    ← 自動建立的執行紀錄
├── .env                     ← API keys（不 commit！）
├── .env.example             ← 範本
└── .gitignore
```

---

## 三、待辦任務（按優先順序）

### TASK 1：Git 初始化 【立即執行】
```bash
cd D:\AI\Claude_agent\daily-knowledge
git init
git add CLAUDE.md .gitignore .env.example history.json scripts/daily_update.py scripts/setup_scheduler.py
git commit -m "init: project structure and core scripts"
```

### TASK 2：複製 HTML 【立即執行】
```bash
python scripts\copy_html_once.py
```
若腳本找不到檔案，手動從 Cowork 輸出資料夾複製：
- 來源：`C:\Users\User\AppData\Roaming\Claude\local-agent-mode-sessions\...\outputs\daily-knowledge-v4.html`
- 目標：`D:\AI\Claude_agent\daily-knowledge\index.html`

### TASK 3：將 index.html 改為 fetch JSON 架構 【核心任務】

目前 index.html 把所有卡片硬編碼在 HTML 裡（約 1060 行）。
需要改成：頁面載入時自動 fetch `data/YYYY-MM-DD.json` 並動態渲染。

**改造步驟：**

1. 在 `<script>` 開頭加入 fetch 邏輯：
```javascript
async function loadTodayData() {
  const today = new Date().toISOString().split('T')[0]; // 'YYYY-MM-DD'
  try {
    const res = await fetch(`data/${today}.json`);
    if (!res.ok) {
      // fallback：找最近一份 JSON
      const hist = await fetch('history.json').then(r => r.json());
      const last = hist.entries[hist.entries.length - 1]?.date;
      if (last) {
        const res2 = await fetch(`data/${last}.json`);
        return await res2.json();
      }
    }
    return await res.json();
  } catch(e) {
    console.error('載入資料失敗', e);
    return null;
  }
}
```

2. JSON 讀進來後，用 `data.cards` 陣列取代原本 `const CARDS = [...]` 的硬編碼內容。

3. 保留現有的 `renderCatbar()`、`doSearch()`、`applyFz()`、Modal 等所有 UI 邏輯，只改資料來源。

4. **JSON 格式**（`data/YYYY-MM-DD.json`）：
```json
{
  "date": "2026-06-06",
  "mode": "paper",
  "paper_date": "2026-06-06",
  "cards": [
    {
      "id": "ai-2606",
      "domain": "ai",
      "day": "2026-06-06",
      "author": "Zhang et al. 2026",
      "ref": "arXiv:2606.04036",
      "url": "https://arxiv.org/abs/2606.04036",
      "color": "#667eea",
      "illus": "<svg viewBox=\"0 0 200 120\">...</svg>",
      "title":   {"zh-TW":"標題","en":"Title","zh-CN":"标题","ja":"タイトル","ko":"제목"},
      "tag":     {"zh-TW":"🤖 AI","en":"🤖 AI","zh-CN":"🤖 AI","ja":"🤖 AI","ko":"🤖 AI"},
      "tech":    {"zh-TW":"技術說明","en":"Tech explanation","zh-CN":"技术说明","ja":"技術説明","ko":"기술 설명"},
      "plain":   {"zh-TW":"白話解釋","en":"Plain English","zh-CN":"白话","ja":"わかりやすく","ko":"쉬운 설명"},
      "insight": {"zh-TW":"💡 洞見","en":"💡 Insight","zh-CN":"💡 洞见","ja":"💡 洞察","ko":"💡 통찰"}
    }
  ]
}
```

5. 原本 T 物件中的 `cards` 區塊（每張卡片的多語言文字）改為從 JSON 的 card 物件讀取：
```javascript
// 舊：t['ai-2606'].title
// 新：card.title[curLang]
```

6. 完成後 git commit：
```bash
git add index.html
git commit -m "feat: convert to fetch-JSON data-driven architecture"
```

### TASK 4：測試 daily_update.py

確認環境變數 `ANTHROPIC_API_KEY` 已設定，然後：
```bash
cd D:\AI\Claude_agent\daily-knowledge
python scripts\daily_update.py
```
正常執行後應產生 `data/2026-06-06.json`，並更新 `history.json`。

若出現 `anthropic` 找不到：
```bash
pip install anthropic
```

### TASK 5：安裝排程（需管理員）

以「系統管理員」身分開啟命令提示字元：
```bash
cd D:\AI\Claude_agent\daily-knowledge
python scripts\setup_scheduler.py
```
這會建立每天凌晨 3:00 自動喚醒並執行的排程任務。

### TASK 6：建立 gen_illustration.py

功能：根據論文 domain 和內容，生成對應的 SVG 插圖（200×120）。
存放路徑：`scripts/gen_illustration.py`
介面：`generate_illus(card: dict) -> str`（回傳 SVG 字串）

### TASK 7：建立 post_instagram.py（等 token）

需要環境變數：
- `IG_ACCESS_TOKEN`
- `IG_BUSINESS_ID`

---

## 四、重要規則

| 規則 | 說明 |
|------|------|
| ❌ 禁止硬編碼 API key | 統一用 `os.environ["ANTHROPIC_API_KEY"]` |
| ❌ 禁止 `input()` | daily_update.py 全自動，不可有任何互動 |
| ❌ 禁止 commit `.env` | 已加入 .gitignore |
| ✅ 每次修改後 commit | 附上有意義的 commit message |
| ✅ 檢查 JS 語法 | 修改 index.html 後執行 `node --check` 驗證 |

---

## 五、arXiv 日期規則

| 今天星期 | 卡片日期 |
|----------|---------|
| 週一 | 上週五（-3天）|
| 週二～五 | 今天 |
| 週六～日 | 趣知模式，今天日期 |

arXiv 週末不出版新論文。

---

## 六、domain 顏色對照

| domain | emoji | 顏色 |
|--------|-------|------|
| ai | 🤖 | #667eea |
| bio | 🧬 | #48bb78 |
| phys | ⚛️ | #ed8936 |
| neuro | 🧠 | #9f7aea |
| health | 🏥 | #fc8181 |
| space | 🌌 | #4299e1 |
| chem | 🧪 | #f6e05e |
| tech | 📶 | #68d391 |
| ocean | 🦈 | #76e4f7 |
| nature | 🐠 | #fbd38d |
| fin | 💰 | #f687b3 |
| arch | 🏛️ | #a0aec0 |

---

## 七、目前狀態（2026-06-06）

### ✅ 已完成
- index.html：全功能網頁（5語言、搜尋、字體縮放、深色模式、Splash 動畫）
- scripts/daily_update.py：完整自動化腳本
- scripts/setup_scheduler.py：Windows Task Scheduler with WakeToRun
- history.json：有 6/1、6/2、6/3 三天紀錄
- CLAUDE.md：本文件

### ❌ 待完成
- TASK 1：git init
- TASK 2：複製 HTML → index.html
- TASK 3：index.html 改為 fetch JSON 架構（最重要）
- TASK 4：測試 daily_update.py
- TASK 5：安裝排程
- TASK 6：gen_illustration.py
- TASK 7：post_instagram.py

---

## 八、分工

| 任務 | 負責 |
|------|------|
| 寫程式、改 HTML、git 操作 | Claude Code |
| 複雜 SVG 插圖、Canva 設計 | Cowork Claude |
| Instagram 策略、內容審核 | Cowork Claude |
| 快速問題回答 | Cowork Claude |
