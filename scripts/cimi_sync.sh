#!/bin/bash
# cimi_sync.sh — 次幂数据同步脚本的 bash 包装
# 用法：./cimi_sync.sh {check-balance | account-info | today-articles | history-articles | sync-all | dry-run}

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3 || echo /usr/bin/python3)"

# 优先用 venv（如果有），否则用系统 python3
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python3"
fi

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN" cimi_sync.py "$@"
