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
  python3 cimi_sync.py search-articles "AI 自动化"  # 微信搜一搜（找对标 0.05元）
  python3 cimi_sync.py wechat-hot         # 微信爆款（0.10元）
  python3 cimi_sync.py toutiao-hot        # 头条爆款（0.10元）
  python3 cimi_sync.py hot-ranking        # 网络热榜（0.01元）

⚠️  成本控制：脚本会在月底用满 CIMI_MONTHLY_BUDGET 时自动停止
📦  凭据从 ~/.config/second-brain/cimi.env 读取，不进 vault
📝  数据追加到 vault/30_领域/公众号运营/MOC.md 的"数据轨迹"段

Created: 2026-07-16
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error, parse

# ============================================================
#  Config
# ============================================================
API_HOST = "https://www.cimidata.com/"  # 2026-07-16 修正：原 host http://api.cimidata.com 已 404；末尾 / 防止与 endpoint 拼成 comapi/...
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

def cimi_curl(method, url, payload=None, token=None):
    """通过 subprocess + curl 调次幂 API（绕过 Python 3.14 urllib 的 SSL EOF bug）

    - method: 'GET' / 'POST'
    - url: 完整 URL（可带 query string）
    - payload: dict（POST 时序列化为 JSON body，GET 时作 query string）
    """
    cmd = ["curl", "-s", "-X", method]
    if method == "POST":
        cmd += ["-H", "Content-Type: application/json"]
        if payload:
            cmd += ["-d", json.dumps(payload, ensure_ascii=False)]
    if token:
        cmd += ["--url", f"{url}{'&' if '?' in url else '?'}access_token={token}"]
    elif payload and method == "GET":
        from urllib.parse import urlencode
        cmd += ["--url", f"{url}{'&' if '?' in url else '?'}{urlencode(payload)}"]
    else:
        cmd += ["--url", url]
    cmd += ["--max-time", "20"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(out.stdout) if out.stdout else None
    except Exception:
        return {"code": -1, "msg": f"非 JSON: {out.stdout[:200]}", "stderr": out.stderr[:200]}


def get_token(cfg, force=False):
    """次幂数据 POST /api/token 换 access_token
    body: {"app_id": "...", "app_secret": "..."}
    缓存到 ~/.config/second-brain/cimi_token.json
    """
    import base64
    token_file = Path.home() / ".config" / "second-brain" / "cimi_token.json"
    if not force and token_file.exists():
        try:
            cached = json.loads(token_file.read_text())
            if cached.get("expires_at", 0) > time.time() + 60:
                return cached["access_token"]
        except Exception:
            pass
    url = f"{API_HOST}api/token"
    result = cimi_curl("POST", url, payload={
        "app_id": cfg["CIMI_APPID"],
        "app_secret": cfg["CIMI_SECRET"],
    })
    if result and result.get("code") == 200 and result.get("data", {}).get("access_token"):
        token = result["data"]["access_token"]
        expires_in = result["data"].get("expires_in", 7200)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(json.dumps({
            "access_token": token,
            "expires_at": time.time() + expires_in,
        }))
        return token
    raise RuntimeError(f"换 token 失败: {result}")


def call_api(cfg, endpoint, payload=None, method="POST"):
    """通用请求（access_token 通过 query string 鉴权）

    endpoint 格式：'api/v2/accounts/search'（无前导 /，跟 host 直接拼）
    method: POST（业务默认）/ GET
    """
    token = get_token(cfg)
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]
    url = f"{API_HOST}{endpoint}"
    if method == "GET" and payload:
        # GET 请求把参数拼到 URL
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(payload)}"
        payload = None
    return cimi_curl(method, url, payload=payload, token=token)


def estimate_cost(endpoint):
    return PRICE_TABLE.get(endpoint, 0.05)

# ============================================================
#  Commands
# ============================================================
def cmd_check_balance(cfg, state):
    """次幂 MCP 用 GET /api/v3/hotrank + channel_id=1 附带返回余额（实测）"""
    print("🔍 查询余额（免费，走 hotrank 接口）...")
    token = get_token(cfg)
    out = cimi_curl("GET", f"{API_HOST}api/v3/hotrank?channel_id=1&access_token={token}")
    if out and out.get("code") == 200:
        bal = out.get("balance", "?")
        print(f"💰 账户余额: {bal} 次")
        # 同时也输出热门第 1 条作为「最近一次访问」证明
        data = out.get("data", [])
        if data:
            first = data[0]
            print(f"🔥 当前微博 Top1: {first.get('title','?')[:50]}（热度 {first.get('hot','?')}）")
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False) if out else "❌ 无响应")
    print(f"\n本月已花: ¥{state.get('spend', 0):.2f} / ¥{cfg.get('CIMI_MONTHLY_BUDGET', '10')}")
    return out

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

# ============================================================
#  找对标账号专用（2026-07-16 新增）
# ============================================================
def cmd_search_articles(cfg, state, keyword, page=1):
    """微信搜一搜（公开 API，按关键词搜公众号文章 → 输出包含账号名）

    用法: cimi_sync.py search-articles "AI 自动化" [页数=1]
    单价: 0.05 元/次
    """
    print(f"🔍 微信搜一搜：「{keyword}」第 {page} 页...")
    cost = estimate_cost("search_articles_wechat")
    check_budget(cfg, state, cost)
    res = call_api(cfg, "api/v3/articles/search", {
        "keyword": keyword,
        "page": page,
        "page_size": 20,
    })
    # search 接口是 POST + body
    state = record_call(state, "search_articles_wechat", cost)
    save_state(state)
    if not res:
        print("❌ 无响应")
        return
    data = res.get("data", {})
    items = data.get("items") or data.get("list") or []
    print(f"📊 命中 {len(items)} 条\n")
    if items:
        print(f"{'公众号名':<20} {'文章标题':<40} {'发布时间':<12} {'阅读量':>8}")
        print("-" * 90)
        seen_accounts = set()
        for item in items:
            account = item.get("account_name") or item.get("nickname") or item.get("公众号") or "?"
            title = item.get("title", "")[:38]
            published = (item.get("publish_time") or item.get("publish_time_str") or "")[:10]
            read_count = item.get("read_count", item.get("read", 0))
            print(f"{account:<20} {title:<40} {published:<12} {read_count:>8}")
            seen_accounts.add(account)
        print(f"\n📌 去重后公众号候选：{len(seen_accounts)} 个")
        for a in sorted(seen_accounts):
            print(f"   • {a}")
    print(f"\n💰 本次 ¥{cost:.2f}，本月累计 ¥{state.get('spend', 0):.2f}")
    # 把结果存到 vault 供师傅后续用
    out = Path("/tmp/cimi_search_last.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"📄 原始 JSON: {out}")


def cmd_wechat_hot(cfg, state):
    """微信爆款文章（按分类）
    用法: cimi_sync.py wechat-hot [分类=科技]
    单价: 0.10 元/次
    """
    cat = sys.argv[2] if len(sys.argv) > 2 else "科技"
    print(f"🔥 微信爆款文章：分类「{cat}」...")
    cost = estimate_cost("get_wechat_hot_articles")
    check_budget(cfg, state, cost)
    res = call_api(cfg, "api/v2/hot/articles", {"category": cat})
    state = record_call(state, "get_wechat_hot_articles", cost)
    save_state(state)
    if not res:
        print("❌ 无响应")
        return
    data = res.get("data", {})
    items = data if isinstance(data, list) else data.get("items", [])
    print(f"📊 共 {len(items)} 条爆款\n")
    for i, item in enumerate(items[:10], 1):
        title = item.get("title", "")[:50]
        account = item.get("account_name") or item.get("nickname", "?")
        read = item.get("read_count", 0)
        print(f"{i:2d}. [{account}] {title}（阅读 {read}）")
    print(f"\n💰 本次 ¥{cost:.2f}，本月累计 ¥{state.get('spend', 0):.2f}")


def cmd_toutiao_hot(cfg, state):
    """头条爆款文章"""
    print(f"🔥 头条爆款文章...")
    cost = estimate_cost("get_toutiao_hot_articles")
    check_budget(cfg, state, cost)
    res = call_api(cfg, "api/v2/hot/tt/articles", {})
    state = record_call(state, "get_toutiao_hot_articles", cost)
    save_state(state)
    print(json.dumps(res, indent=2, ensure_ascii=False) if res else "❌ 无响应")
    print(f"\n💰 本次 ¥{cost:.2f}")


def cmd_hot_ranking(cfg, state):
    """网络热榜（最便宜，0.01 元/次）"""
    print(f"🌐 网络热榜...")
    cost = estimate_cost("get_hot_ranking")
    check_budget(cfg, state, cost)
    res = call_api(cfg, "api/v3/hotrank", {})
    state = record_call(state, "get_hot_ranking", cost)
    save_state(state)
    if not res:
        print("❌ 无响应")
        return
    data = res.get("data", {})
    items = data if isinstance(data, list) else data.get("items", [])
    print(f"📊 共 {len(items)} 条\n")
    for i, item in enumerate(items[:15], 1):
        title = item.get("title") or item.get("word", "")[:60]
        hot = item.get("hot") or item.get("hot_value", 0)
        print(f"{i:2d}. {title} (热度 {hot})")
    print(f"\n💰 本次 ¥{cost:.2f}")


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
    elif cmd == "search-articles":
        # 微信搜一搜（找对标账号用）
        if len(sys.argv) < 3:
            print("用法: cimi_sync.py search-articles <关键词> [页数=1]")
            sys.exit(1)
        keyword = sys.argv[2]
        page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        cmd_search_articles(cfg, state, keyword, page)
    elif cmd == "wechat-hot":
        cmd_wechat_hot(cfg, state)
    elif cmd == "toutiao-hot":
        cmd_toutiao_hot(cfg, state)
    elif cmd == "hot-ranking":
        cmd_hot_ranking(cfg, state)
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
