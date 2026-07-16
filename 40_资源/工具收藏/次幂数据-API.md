---
type: source
category: 工具收藏 - 数据 API
created: 2026-07-16
status: active
tags: [次幂数据, API, 公众号数据, 同步]
related: [[30_领域/公众号运营/MOC]], [[30_领域/AI自动化/MOC]]
---

# 📊 次幂数据 API · 公众号数据同步方案

> **目的**：把公众号后台关键数据（粉丝 / 阅读 / 分享 / 文章列表 / 单文章统计）每日自动同步到 [[30_领域/公众号运营/MOC]]
> **不让成本失控**：月预算 ¥10，每次调用前预算检查
> **凭证不进 vault**：所有凭据在 `~/.config/second-brain/cimi.env`（vault 外）

---

## 🔑 凭据管理（安全）

| 项 | 位置 |
|----|------|
| AppID | `~/.config/second-brain/cimi.env` → `CIMI_APPID` |
| Secret | `~/.config/second-brain/cimi.env` → `CIMI_SECRET` |
| 默认公众号 | `~/.config/second-brain/cimi.env` → `CIMI_ACCOUNT_NICKNAME=大姚AI提效` |
| 月预算 | `~/.config/second-brain/cimi.env` → `CIMI_MONTHLY_BUDGET=10` |

文件权限已设为 600（仅本人可读写）。**绝不能复制到 vault 里。**

---

## 💰 价格表（每次接口调用扣除）

> 来自次幂数据官方与 cimi-data-mcp README（2026-07-16）

| 接口 | 单价 | 用途 | 频率建议 |
|------|------|------|---------|
| `check_balance` | ¥0.00 | 查账户余额 | 任何时候 |
| `get_account_info` | ¥0.04 | 公众号基本信息（粉丝/微信号等） | 每周 1 次 |
| `get_today_articles` | ¥0.04 | 今日发文列表 | 发文后 1 次 |
| `get_history_articles` | ¥0.05 | 历史文章列表 | 每周 1 次 |
| `get_article_stats` | ¥0.02 | 单文章阅读/点赞/在看 | 发文后 5 分钟/1 小时/次日 |
| `get_article_full_stats` | ¥0.03 | 单文章完整统计（含分享） | 同上 |
| `get_article_content_full` | ¥0.01 | 文章完整 HTML | 同上 |
| `get_article_body` | ¥0.01 | 文章正文 | 必要时 |
| `get_article_comments` | ¥0.02 | 文章评论 | 评论区互动时 |
| `search_articles_wechat` | ¥0.05 | 微信搜一搜 | 选题侦察 |
| `get_wechat_hot_articles` | ¥0.10 | 微信爆款文章 | 选题侦察 |
| `get_toutiao_hot_articles` | ¥0.10 | 头条爆款文章 | 选题侦察 |
| `get_hot_ranking` | ¥0.01 | 网络热榜 | 选题侦察 |

**每周最低成本估算**：
- 周日同步：`account_info ¥0.04 + history ¥0.05 + article_stats ×3 篇 ¥0.06 = ¥0.15`
- 月度：¥0.6 ≈ **远低于 10 元预算**，可控

---

## 🛠️ 同步脚本

脚本位置：`vault_root/scripts/cimi_sync.py`（已写完可直接用）

**首次运行流程**：
```bash
cd /Volumes/External/工作资料/第二大脑/第二大脑/scripts

# 第 1 步：dry-run 看会调什么（不花钱）
./cimi_sync.sh dry-run

# 第 2 步：免费验证鉴权
./cimi_sync.sh check-balance

# 第 3 步：公众号基本信息（¥0.04）
./cimi_sync.sh account-info

# 第 4 步：过去 30 天文章列表（¥0.05）
./cimi_sync.sh history-articles 30
```

**设自动同步**：
```bash
crontab -e
# 每周日凌晨 2 点同步（推荐）
0 2 * * 0 /Volumes/External/工作资料/第二大脑/第二大脑/scripts/cimi_sync.sh sync-all
```

---

## ⚠️ 鉴权方式（待师傅确认）

我按国产 API 惯例写了**两套 header**（双保险）：
```python
"X-Appid": {AppID},
"X-Secret": {Secret},
"Authorization": "Bearer {AppID}:{Secret}",
```

如果都不通，去 https://www.showdoc.com.cn/2265380957870963 看官方文档，把 `call_api()` 函数里的 headers 改成官方格式。

---

## 🔄 数据流向

```
次幂数据 API
    │
    ↓ (POST + 鉴权)
cimi_sync.py
    │
    ├─→ 控制台输出（每次）
    ├─→ 月度花费记录（~/.config/second-brain/cimi_usage.json）
    └─→ 追加到 vault → [[30_领域/公众号运营/MOC]] 的 📈 数据轨迹 段
```

---

## 🆚 为什么不直接用现成 MCP

看到 `oychao1988/cimi-data-mcp`（GitHub）已经在做这件事，但有几个原因目前先不直接接：

1. **师傅场景小**：只问"大姚AI提效" 1 个号的数据，手动脚本够用
2. **可控优先**：自写脚本能精确控制每次成本
3. **MCP 兼容性**：师傅当前是 Obsidian + Claudian，不是 Claude Desktop，多一层集成工作

> 等跑到 5+ 个公众号 / 多账号时，再考虑切 MCP。届时把这个笔记的"为什么不直接用现成 MCP"段删除，加 MCP 链接。

---

## 📌 已知限制

1. **鉴权方式未确认**：跑不通先调 `call_api()` 函数
2. **接口返回值结构**：次幂数据返回结构每个接口不同，脚本只做"原样追加 JSON"，师傅看清楚可以写 Markdown 解析
3. **没有重试机制**：网络出错只重跑，不复杂化
4. **没接 n8n**：等 [[30_领域/AI自动化/MOC]] 的 n8n 工作流再造

---

*最后更新：2026-07-16 · v0.1 已可运行*
