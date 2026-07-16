# 🧠 大姚的第二大脑（second-brain-vault）

> 一个把"我现在想做的事"和"我学到的/读到的/想到的东西"统一管理的地方。
> 目的：**少回忆，多决策；少重复，多复用**。

---

## ⚡ 30 秒上手

1. **每天早上** → 打开 `10_日记/今日/`，写今天最重要的一件事
2. **任何瞬间冒出来的想法** → 丢到 `00_收件箱/`，**不在当时整理**
3. **每天晚上** → 花 5 分钟，清空收件箱（用 Claudian 一句话，见 `90_模板/Claudian话术包.md`）
4. **每周日** → 花 30 分钟，做周日整理 SOP
5. **每月 1 号** → 做一次月度复盘

---

## 🗂️ 目录地图（PARA × CODE 双轨）

```
📥 00_收件箱        所有临时想法、链接、灵感（私有，不提交）
📅 10_日记          每日笔记，工作日志、决策
🚀 20_项目          有截止日期、有具体产出 的事
🌱 30_领域          长期负责的方向（公众号运营 / AI自动化 / 副业探索 / 个人成长）
📚 40_资源          主题资料（文章笔记、工具收藏、课程书、剪藏归档）
📤 50_输出          对外的成品（公众号文章、复盘）
📋 90_模板          4 套核心模板 + 使用手册 + Claudian 话术包
🗄️ 99_归档          已完结的项目和领域
```

完整设计说明 → [`00_主页.md`](00_主页.md)

---

## 🤖 让 AI 怎么用这个 Vault

📜 **核心规则** → [`00_AI协作规则.md`](00_AI协作规则.md)
🛠️ **12 句现成话术** → [`90_模板/Claudian话术包.md`](90_模板/Claudian话术包.md)

Claude / Claudian 帮你：

- ✅ 清空收件箱（提议去向，你 ✅/❌）
- ✅ 补双向链接
- ✅ 周复盘快照
- ✅ 周日整理 SOP
- ✅ 找主题笔记（飞书 + vault 全搜）
- ✅ 月度复盘
- ✅ 紧急收敛（卡壳时用）
- ✅ 造一条新原子（进 Hermes 13 库）
- ✅ 看选题池进度（08 库）
- ✅ 发布后回填 09 队列
- ✅ 整理 Clippings 剪藏
- ✅ 按 Hermes 出文（13 步 SOP）

---

## 🛟 周备份（脚本）

```bash
./backup-vault.sh             # 立即跑一次
crontab -e                    # 设每周日 9 点自动跑
0 9 * * 1 ./backup-vault.sh   # crontab 行
```

备份位置：`vault/.attachments/backups/`，保留 30 天。

---

## 🔌 scripts/ 目录

vault 根目录的 `scripts/` 装了一组轻量 Python 脚本（≤300 行），对接外部 API：

| 脚本 | 用途 |
|------|------|
| `feishu.py` | 飞书 16 表多维表格 CRUD（选题/原子库/案例库 等） |
| `hermes.py` | Hermes 13 步 SOP 接口 |
| `cimi_sync.py` | 次幂数据 API 同步（公众号后台数据） |
| `image_gen.py` | 中转站图像 API 封装 |
| `article_to_html.py` | Markdown + base64 内嵌图 → 单文件 HTML |
| `clippings_sort.py` | 扫 Clippings/ 待归档 → 提议归宿 |

详见 [`scripts/README.md`](scripts/README.md)

**安全约定**：所有 API 凭据放在 vault 外部（`~/.config/second-brain/*.env`），**不进 vault，不进 git**。

---

## 🚧 用 git 同步（多设备使用）

```bash
git clone git@github.com:yaoywei/second-brain-vault.git ~/second-brain
cd ~/second-brain

# 第一次使用：把 00_收件箱/ .attachments/ 等私有内容放在外部
# 同步策略：每个设备都有自己的私密目录
```

⚠️ **本仓库是公开的**，请勿提交：

- ❌ 任何个人密钥、API token
- ❌ 微信/公众号隐私数据
- ❌ 个人财务、健康等敏感信息

## 📌 重要原则

> ❌ 不要追求完美分类 — 4 个桶够用，别再细分
> ✅ 一张笔记一个观点 — 别把 3000 字塞一张卡
> 🚫 永远不要"先把所有笔记先整理好再说" — 现在就想写就写
> 🔗 链接 > 分类 — 能 wiki-link 就别开新文件夹
> 🤖 AI 是队友不是管家 — 让 AI 帮你清收件箱、做归纳，**但判断必须你来下**

---

## 📚 一页纸规则

- [`00_主页.md`](00_主页.md) ← 你正在看
- [`90_模板/使用手册.md`](90_模板/使用手册.md) ← 详细 1 页使用规则
- [`00_AI协作规则.md`](00_AI协作规则.md) ← 给 AI 看的"厂规"
- [`90_模板/Claudian话术包.md`](90_模板/Claudian话术包.md) ← 12 句现成 AI 话术
- [`scripts/README.md`](scripts/README.md) ← 6 个本地化脚本的入口

---

*最后更新：2026-07-16 · v0.2 接入 Herm
es + 飞书 + Clippings*
*仓库是骨架 + 公开内容，私人数据请放在 `00_收件箱/`、`Clippings/`、`.attachments/` 这些已在 .gitignore 排除的目录*
