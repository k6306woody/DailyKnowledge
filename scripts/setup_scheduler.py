#!/usr/bin/env python3
"""
setup_scheduler.py — 建立 Windows 工作排程器任務
每天凌晨 3:00 自動喚醒電腦並執行 daily_update.py
需要以「系統管理員」身分執行一次
"""

import io
import os
import sys
import subprocess
from pathlib import Path

# 確保 stdout 以 UTF-8 輸出（Windows cp950 預設會擋 emoji）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent.parent   # D:\AI\Claude_agent\daily-knowledge
SCRIPTS_DIR = ROOT / "scripts"
PYTHON_EXE = sys.executable           # 目前 Python 的路徑

TASK_NAME = "DailyKnowledgeUpdate"
TASK_XML = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>每日新知網頁自動更新 - 凌晨3點喚醒執行</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T03:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{PYTHON_EXE}</Command>
      <Arguments>"{SCRIPTS_DIR / 'daily_update.py'}"</Arguments>
      <WorkingDirectory>{ROOT}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""


def check_admin():
    """確認是否以管理員身分執行"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def install_task():
    # 寫 XML 到暫存檔
    xml_path = ROOT / "scripts" / f"{TASK_NAME}.xml"
    xml_path.write_text(TASK_XML, encoding="utf-16")
    print(f"✅ XML 已寫出：{xml_path}")

    # 先刪除舊任務（若存在）
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )

    # 匯入任務
    result = subprocess.run(
        ["schtasks", "/Create", "/XML", str(xml_path), "/TN", TASK_NAME],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"✅ 排程任務「{TASK_NAME}」建立成功！")
        print(f"   每天凌晨 3:00 自動喚醒執行 daily_update.py")
    else:
        print(f"❌ 建立失敗：{result.stderr}")
        print("   請確認以系統管理員身分執行本腳本")
        sys.exit(1)

    # 驗證
    verify = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("\n── 任務詳情 ──")
    print(verify.stdout)


def setup_env():
    """提示使用者設定環境變數"""
    print("\n── 環境變數設定 ──")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        print(f"✅ ANTHROPIC_API_KEY 已設定（{key[:8]}...）")
    else:
        print("⚠️  ANTHROPIC_API_KEY 尚未設定！")
        print("   請在 Windows 系統環境變數中設定：")
        print("   控制台 → 系統 → 進階系統設定 → 環境變數")
        print("   新增系統變數：ANTHROPIC_API_KEY = sk-ant-...")
        print("")
        print("   或執行（以管理員 PowerShell）：")
        print(f'   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-你的KEY","Machine")')


def main():
    print("=" * 60)
    print(f"Daily Knowledge — 排程器安裝")
    print(f"Python：{PYTHON_EXE}")
    print(f"腳本：{SCRIPTS_DIR / 'daily_update.py'}")
    print("=" * 60)

    if not check_admin():
        print("⚠️  非管理員模式（WakeToRun 喚醒功能可能需要管理員才能生效）")
        print("   繼續安裝排程...")


    install_task()
    setup_env()

    print("\n✅ 設定完成！排程任務將在每天凌晨 3:00 自動執行。")
    print("   電腦可以正常休眠，系統會自動喚醒。")


if __name__ == "__main__":
    main()
