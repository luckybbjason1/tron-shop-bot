#!/bin/bash
# Telegram Shop Bot 自动备份脚本
# 备份数据库和配置文件

BACKUP_DIR="$HOME/tg-shop-bot/backups"
DATA_DIR="$HOME/tg-shop-bot/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份文件
echo "📦 开始备份..."

# 创建备份
tar -czf "$BACKUP_FILE" \
    -C "$HOME/tg-shop-bot" \
    data/shop.db \
    data/accounts.json \
    bot/main.py \
    bot/database.py \
    .env 2>/dev/null

# 检查是否成功
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ 备份完成: $BACKUP_FILE ($SIZE)"
    
    # 删除 7 天前的备份
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
    echo "🗑️ 已清理 7 天前的旧备份"
else
    echo "❌ 备份失败"
    exit 1
fi
