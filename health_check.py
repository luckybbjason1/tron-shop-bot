#!/usr/bin/env python3
"""
健康检查脚本
检查 Bot 和数据库状态
"""
import os
import sys
import sqlite3
import json
import urllib.request
from datetime import datetime

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'shop.db')
GITHUB_URL = 'https://raw.githubusercontent.com/luckybbjason1/tron-shop-bot/main/data/accounts.json'

def check_bot():
    """检查 Bot 是否可用"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            if data.get('ok'):
                return True, f"Bot 正常: {data['result']['username']}"
    except Exception as e:
        return False, f"Bot 错误: {e}"
    return False, "Bot 检查失败"

def check_database():
    """检查数据库"""
    try:
        if not os.path.exists(DB_PATH):
            return False, "数据库文件不存在"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查账号表
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        
        # 检查最近备份
        cursor.execute("SELECT MAX(created_at) FROM accounts")
        last_update = cursor.fetchone()[0]
        
        conn.close()
        
        return True, f"数据库正常: {count} 个账号"
    except Exception as e:
        return False, f"数据库错误: {e}"

def check_github():
    """检查 GitHub 连接"""
    try:
        req = urllib.request.Request(GITHUB_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            count = len(data.get('accounts', []))
            return True, f"GitHub 正常: {count} 个账号"
    except Exception as e:
        return False, f"GitHub 错误: {e}"

def main():
    """主函数"""
    print(f"[{datetime.now()}] 健康检查开始")
    print("")
    
    checks = [
        ("Bot API", check_bot),
        ("数据库", check_database),
        ("GitHub", check_github),
    ]
    
    all_ok = True
    for name, check_func in checks:
        ok, msg = check_func()
        status = "✅" if ok else "❌"
        print(f"{status} {name}: {msg}")
        if not ok:
            all_ok = False
    
    print("")
    if all_ok:
        print("✅ 所有检查通过")
    else:
        print("⚠️ 部分检查失败")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
