#!/usr/bin/env python3
"""
cimi_sync.py — 从次幂数据同步公众号数据到本 vault
======================================================================
用法：
  python3 cimi_sync.py check-balance     # 只查余额（免费）
  python3 cimi_sync.py account-info      # 公众号基本信息（0.04元）
  python3 cimi_sync.py today-articles    # 今日发文（0.04元）
  python3 cimi_sync.py history-articles  # 历史文章列表（0.05元/页）
  python3 cimi_sync.py article-stats URL # 单文章阅读/点赞（0.02元）
  python3 cimi_sync.py sync-all          # 跑一次完整快照
  python3 cimi_sync.py dry-run           # 看会调哪些，不真发

⚠️  成本控制：脚本会在月底用满 CIMI_MONTHLY_BUDGET 时自动停止
📦  凭据从 ~/.config/second-brain/cimi.env 读取，不进 vault
📝  数据追加到 vault/30_领域/公众号运营/MOC.md 的"数据轨迹"段

Created: 2026-07-16
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error, parse

# ============================================================
#  Config
# ============================================================
API_HOST = "http://api.cimidata.com"
ENV_FILE = Path.home() / ".config" / "second-brain" / "cimi.env"
VAULT_ROOT = Path("/Volumes/External/工作资料/第二大脑/第二大脑")
MOC_FILE = VAULT_ROOT / "30_领域" / "公众号运营" / "MOC.md"
STATE_FILE = Path.home() / ".config" / "second-brain" / "cimi_usage.json"

# 接口定价（来自 cimi-data-mcp README 与官方文档，2026-07-16）
PRICE_TABLE = {
    "check_balance": 0.00,
    "get_account_info": 0.04,
    "get_today_articles": 0.04,
    "get_history_articles": 0.05,
    "get_article_stats": 0.02,
    "get_article_full_stats": 0.03,
    "get_article_content_full": 0.01,
    "get_article_body": 0.01,
    "get_article_comments": 0.02,
    "search_articles_wechat": 0.05,
    "get_wechat_hot_articles": 0.10,
    "get_toutiao_hot_articles": 0.10,
    "get_hot_ranking": 0.01,
}

# ============================================================
#  Helpers
# ============================================================
def load_env():
    """从 cimi.env 加载凭据"""
    if not ENV_FILE.exists():
        print(f"❌ 凭据文件不存在: {ENV_FILE}")
        print(f"   创建文件并填入: CIMI_APPID / CIMI_SECRET")
        sys.exit(1)
    cfg = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        cfg[k.strip()] = v.strip()
    for k in ("CIMI_APPID", "CIMI_SECRET"):
        if not cfg.get(k):
            print(f"❌ {k} 缺失，请编辑 {ENV_FILE}")
            sys.exit(1)
    return cfg

def load_state():
    """加载本月调用计数（用于预算控制）"""
    if not STATE_FILE.exists():
        return {"month": "", "calls": {}}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"month": "", "calls": {}}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def record_call(state, endpoint, cost):
    """记录一次调用 + 扣费"""
    month = datetime.now().strftime("%Y-%m")
    if state.get("month") != month:
        state = {"month": month, "calls": {}, "spend": 0.0}
    state["calls"][endpoint] = state["calls"].get(endpoint, 0) + 1
    state["spend"] = round(state.get("spend", 0.0) + cost, 4)
    return state

def check_budget(cfg, state, will_spend):
    """预算超限直接拒绝"""
    budget = float(cfg.get("CIMI_MONTHLY_BUDGET", "10"))
    spent = state.get("spend", 0.0) if state.get("month") == datetime.now().strftime("%Y-%m") else 0.0
    if spent + will_spend > budget:
        print(f"❌ 月预算上限 ¥{budget:.2f}：已花 ¥{spent:.2f}，本次 ¥{will_spend:.2f} 会超。")
        print(f"   提高 CIMI_MONTHLY_BUDGET 或下个月再跑")
        sys.exit(2)
    return spent

def call_api(cfg, endpoint, payload=None):
    """通用 POST 请求
    注：次幂数据鉴权方式文档未公开，默认按国产 API 惯例用 X-Appid + X-Secret header
    如不通请到 https://www.showdoc.com.cn/2265380957870963 看官方说明改
    """
    url = f"{API_HOST}/{endpoint}"
    body = json.dumps(payload or {}).encode("utf-8")

    # 优先按官方常见的 token 模式 + fallback 到 header 模式
    headers = {
        "Content-Type": "application/json",
        "X-Appid": cfg["CIMI_APPID"],
        "X-Secret": cfg["CIMI_SECRET"],
        # 次幂常见的形式：Authorization: Bearer {appid}:{secret}
        "Authorization": f"Bearer {cfg['CIMI_APPID']}:{cfg['CIMI_SECRET']}",
        "User-Agent": "second-brain-cimi-sync/0.1",
    }

    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"⚠️  HTTP {e.code}：{body[:200]}")
        return {"code": e.code, "msg": body}
    except Exception as e:
        print(f"⚠️  请求失败: {e}")
        return None

def estimate_cost(endpoint):
    return PRICE_TABLE.get(endpoint, 0.05)

# ============================================================
#  Commands
# ============================================================
def cmd_check_balance(cfg, state):
    print("🔍 查询余额（免费）...")
    res = call_api(cfg, "check_balance")
    print(json.dumps(res, indent=2, ensure_ascii=False) if res else "❌ 无响应")
    print(f"\n本月已花: ¥{state.get('spend', 0):.2f} / ¥{cfg.get('CIMI_MONTHLY_BUDGET', '10')}")
    return res

def cmd_account_info(cfg, state):
    cost = estimate_cost("get_account_info")
    spent = check_budget(cfg, state, cost)
    print(f"📡 公众号基本信息（¥{cost} / 本次¥{cost}，本月累计 ¥{spent:.2f}）...")
    res = call_api(cfg, "get_account_info", {
        "nickname": cfg.get("CIMI_ACCOUNT_NICKNAME", "")
    })
    if res and res.get("code") == 200:
        append_to_moc(res, "account_info")
        state = record_call(state, "get_account_info", cost)
        save_state(state)
        print(f"✅ 已写入 [[30_领域/公众号运营/MOC]]")
    else:
        print(f"⚠️  数据未写入，请检查返回：{json.dumps(res, ensure_ascii=False, indent=2) if res else '空'}")
    return res

def cmd_today_articles(cfg, state):
    cost = estimate_cost("get_today_articles")
    check_budget(cfg, state, cost)
    print(f"📡 今日发文（¥{cost}）...")
    res = call_api(cfg, "get_today_articles", {
        "nickname": cfg.get("CIMI_ACCOUNT_NICKNAME", "")
    })
    if res and res.get("code") == 200:
        append_to_moc(res, "today_articles")
        state = record_call(state, "get_today_articles", cost)
        save_state(state)
    print(json.dumps(res, indent=2, ensure_ascii=False) if res else "❌ 无响应")
    return res

def cmd_history_articles(cfg, state, days=30):
    cost = estimate_cost("get_history_articles")
    check_budget(cfg, state, cost)
    print(f"📡 历史文章列表（近 {days} 天，¥{cost}）...")
    res = call_api(cfg, "get_history_articles", {
        "nickname": cfg.get("CIMI_ACCOUNT_NICKNAME", ""),
        "days": days,
    })
    if res and res.get("code") == 200:
        append_to_moc(res, "history_articles")
        state = record_call(state, "get_history_articles", cost)
        save_state(state)
    print(json.dumps(res, indent=2, ensure_ascii=False) if res else "❌ 无响应")
    return res

def cmd_article_stats(cfg, state, article_url):
    cost = estimate_cost("get_article_stats")
    check_budget(cfg, state, cost)
    print(f"📡 单篇文章统计（¥{cost}）...")
    res = call_api(cfg, "get_article_stats", {"url": article_url})
    if res and res.get("code") == 200:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        state = record_call(state, "get_article_stats", cost)
        save_state(state)
    return res

def cmd_sync_all(cfg, state):
    """一次完整快照：account + today + history + 关键文章 stats
    总成本估算：0.04 + 0.04 + 0.05 + N × 0.02
    """
    print("🔄 跑完整快照... 估算成本：¥0.13 + N×0.02")
    cmd_account_info(cfg, state)
    time.sleep(0.5)
    cmd_today_articles(cfg, state)
    time.sleep(0.5)
    cmd_history_articles(cfg, state, days=30)

def cmd_dry_run(cfg, state):
    print("\n📋 Dry run — 不发请求")
    print(f"   账户:        {cfg.get('CIMI_ACCOUNT_NICKNAME', '?')}")
    print(f"   月预算:      ¥{cfg.get('CIMI_MONTHLY_BUDGET', '10')}")
    print(f"   本月已花:    ¥{state.get('spend', 0):.2f}")
    print(f"   API Host:    {API_HOST}")
    print(f"   MOC 输出:    {MOC_FILE}")
    print(f"   接口定价表：")
    for k, v in PRICE_TABLE.items():
        print(f"      {k:35s} ¥{v:.2f}")

# ============================================================
#  MOC append
# ============================================================
def append_to_moc(payload, source):
    """追加本次同步结果到 [[MOC]]"""
    if not MOC_FILE.exists():
        print(f"⚠️  MOC 不存在: {MOC_FILE}")
        return
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = MOC_FILE.read_text()

    # 找到 📈 数据轨迹 段
    marker = "## 📈 数据轨迹（每月追加）"
    if marker not in text:
        # 添加到文末
        text += f"\n\n{marker}\n\n"
    block = f"\n### {today} · {source}\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
    text = text.replace(marker, marker + block, 1)
    MOC_FILE.write_text(text)
    print(f"📝 已追加到 {MOC_FILE.name}")

# ============================================================
#  Main
# ============================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cfg = load_env()
    state = load_state()
    cmd = sys.argv[1]

    if cmd == "check-balance":
        cmd_check_balance(cfg, state)
    elif cmd == "account-info":
        cmd_account_info(cfg, state)
    elif cmd == "today-articles":
        cmd_today_articles(cfg, state)
    elif cmd == "history-articles":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        cmd_history_articles(cfg, state, days)
    elif cmd == "article-stats":
        if len(sys.argv) < 3:
            print("用法: cimi_sync.py article-stats <URL>")
            sys.exit(1)
        cmd_article_stats(cfg, state, sys.argv[2])
    elif cmd == "sync-all":
        cmd_sync_all(cfg, state)
    elif cmd == "dry-run":
        cmd_dry_run(cfg, state)
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
