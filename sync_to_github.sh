#!/bin/bash
# 同步数据库到 GitHub (可选)
cd ~/tg-shop-bot

# 导出数据库为 JSON
python3 << 'PYEOF'
import sqlite3
import json
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'shop.db')
output_path = 'data/accounts_export.json'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 导出账号
    cursor.execute("SELECT * FROM accounts")
    accounts = [dict(row) for row in cursor.fetchall()]
    
    # 导出订单
    cursor.execute("SELECT * FROM orders")
    orders = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    with open(output_path, 'w') as f:
        json.dump({'accounts': accounts, 'orders': orders}, f, indent=2)
    
    print(f"✅ 导出完成: {len(accounts)} 个账号, {len(orders)} 个订单")
except Exception as e:
    print(f"❌ 导出失败: {e}")
PYEOF

# 提交到 GitHub
git add data/accounts_export.json
git commit -m "Auto sync: $(date +%Y-%m-%d_%H:%M:%S)" 2>/dev/null
git push origin main 2>/dev/null && echo "✅ 已同步到 GitHub" || echo "⚠️ 同步失败 (可能需要网络)"
