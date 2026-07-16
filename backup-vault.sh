#!/bin/bash
# ============================================================================
#  第二大脑 Vault 周备份脚本
#  Usage: ./backup-vault.sh
#  Created: 2026-07-16
#  设置每周自动跑：crontab -e → 0 9 * * 1 /path/to/backup-vault.sh
# ============================================================================

set -e

# === Config ===
VAULT_DIR="/Volumes/External/工作资料/第二大脑/第二大脑"
BACKUP_DIR="${VAULT_DIR}/.attachments/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M")
BACKUP_FILE="${BACKUP_DIR}/vault_backup_${TIMESTAMP}.tar.gz"
RETENTION_DAYS=30  # 保留最近 30 天备份

# === Safety check ===
if [ ! -d "$VAULT_DIR" ]; then
    echo "❌ Vault 目录不存在: $VAULT_DIR"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

# === Backup ===
echo "📦 开始备份：$VAULT_DIR"
echo "   → $BACKUP_FILE"

cd "$(dirname "$VAULT_DIR")"
tar -czf "$BACKUP_FILE" \
    --exclude='.trash' \
    --exclude='.DS_Store' \
    --exclude='.obsidian/workspace*' \
    --exclude='.attachments/backups/*.tar.gz' \
    --exclude='.claude/sessions/*' \
    --exclude='.claudian/sessions/*' \
    "$(basename "$VAULT_DIR")"

# === Result ===
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "✅ 备份完成！"
echo "   文件: $BACKUP_FILE"
echo "   大小: $BACKUP_SIZE"
echo ""

# === Cleanup old backups ===
echo "🧹 清理 $RETENTION_DAYS 天前的备份..."
find "$BACKUP_DIR" -name "vault_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print 2>/dev/null || true
REMAINING=$(ls -1 "$BACKUP_DIR"/vault_backup_*.tar.gz 2>/dev/null | wc -l | tr -d ' ')
echo "   保留备份数: $REMAINING"
echo ""
echo "💡 建议：每周日跑一次，或用 crontab 自动跑："
echo "   crontab -e"
echo "   0 9 * * 1 $VAULT_DIR/backup-vault.sh"
