#!/usr/bin/env python3
"""
自动备份监控脚本
每天运行一次备份
"""
import os
import sys
import time
import schedule
import subprocess
from datetime import datetime

BACKUP_SCRIPT = os.path.join(os.path.dirname(__file__), 'backup.sh')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'backups', 'cron.log')

def run_backup():
    """执行备份"""
    print(f"[{datetime.now()}] 开始自动备份...")
    try:
        result = subprocess.run(
            ['bash', BACKUP_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] ✅ 备份成功")
            print(result.stdout)
        else:
            print(f"[{datetime.now()}] ❌ 备份失败")
            print(result.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 备份错误: {e}")

def main():
    """主函数"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # 立即执行一次
    run_backup()
    
    # 每天 2:00 执行
    schedule.every().day.at("02:00").do(run_backup)
    
    print(f"[{datetime.now()}] 备份监控已启动")
    print("每天 2:00 自动备份")
    
    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
