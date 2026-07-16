---
type: ai-prompts
created: 2026-07-16
tags: [Claudian, AI, 话术, 模板]
related: [[00_AI协作规则]]
---

# 🛠️ Claudian 话术包（直接复制就能用）

> 师傅常对 Claudian 说的 6 句"黑话"。每句都是验证过的高频任务。
> Ctrl+C → Ctrl+V → 改细节。

---

## 1️⃣ 清空收件箱

```
帮我清空 [[00_收件箱]]：
1. 读所有文件，逐条用 3 问归类：
   - 是 [[20_项目/大姚AI提效-公众号/]] 的素材吗？
   - 是 [[30_领域/]] 哪个领域的补充？
   - 只是临时参考 → [[40_资源/]] 对应分类
   - 完全没用 → 删
2. 用 [[90_模板/03_资源笔记]] 或 [[90_模板/04_想法模板]] 创建目标笔记
3. 在原文件头部插入归宿标注：→ [[目标笔记]]
4. 输出清单：原文件 → 归宿，等我 ✅/❌
```

---

## 2️⃣ 补双向链接

```
帮我补双向链接：
1. 读最近 7 天新增的所有 .md 文件
2. 扫描 [[30_领域/]] 的 4 个 MOC，找到内容相关的新笔记
3. 在新笔记的 `related:` 字段加上 wiki-link
4. 在 MOC 的相关章节追加 wiki-link
5. 输出报告：X 个笔记补了链接
```

---

## 3️⃣ 周复盘快照

```
帮我做本周复盘快照：
1. 读 [[10_日记/]] 这周（周X → 周X）所有日记
2. 提炼 3 件事：
   - 做成的事（具体到哪篇、哪个项目）
   - 没做成（原因分类：时间/卡壳/无判断）
   - 学到的 1 个东西
3. 追加到 [[30_领域/公众号运营/MOC]] 的"📅 何时更新这个 MOC"上方
4. 格式：## 周复盘 YYYY-MM-DD ~ MM-DD
```

---

## 4️⃣ 周日整理 SOP

```
帮我做周日整理（30 分钟 SOP）：
1. 检查 [[20_项目/大姚AI提效-公众号/任务清单]]，把过期挪到 Backlog
2. 读 [[40_资源/]] 这周新增的笔记，没写"我的判断"段的补上
3. 跑上面的"周复盘快照"
4. 检查 [[00_收件箱]]，>7 天未处理的做"继续/搁置/归档"建议
5. 输出：本周报告 + 下周 3 个建议动作
```

---

## 5️⃣ 按 Hermes 出文（升级版，v3 接入 Hermes + 飞书）

```
帮我按 Hermes 出文：
1. 选一条 08 库 P0 选题：
   python3 scripts/feishu.py list 08 --filter "优先级,==,P0-先写" --limit 5
2. 拿到 record_id 后取料：
   python3 scripts/hermes.py phase1 --pool-id <recXXX>
3. 判断风格：
   python3 scripts/hermes.py style --keyword "{我这次的方向}"
4. 写之前必读：
   - [[30_领域/AI自动化/Hermes本地化/13步SOP速查]] 的 5 段式
   - /tmp/ai-gzh-platform/references/dayao-writing-prompt.md 或 lead-gen-writing-style.md
5. 写 article.md，硬约束：≥2500字 / ≥2表格 / ≥3配图 / 禁用词 0
6. 自动校验：
   python3 scripts/hermes.py check-warns --article article.md
   python3 scripts/hermes.py check-title --title "..." --digest "..."
7. 写入 [[50_输出/公众号文章/]]，更新 08 库为「写作中」：
   python3 scripts/feishu.py update 08 <recXXX> --field 生产状态 --value "写作中"
```

**详细流程** → [[30_领域/AI自动化/Hermes本地化/13步SOP速查]]

---

## 6️⃣ 找主题笔记（升级版，v3 接入飞书）

```
帮我找关于 {关键词} 的素材：
1. 飞书 13 库（专业原子）优先：
   python3 scripts/feishu.py find 13 "{关键词}"
2. 飞书 08 库（生产选题）：
   python3 scripts/feishu.py find 08 "{关键词}"
3. vault 全搜（笔记）：
   grep -ri "{关键词}" 30_领域/ 40_资源/
4. 输出：飞书 record_id + vault wikilink + 一句话简介
```

---

## 7️⃣ 月度复盘

```
帮我做月度复盘：
1. 读本月所有 [[10_日记/]]
2. 读 [[20_项目/大姚AI提效-公众号/项目主页]] 的"数据轨迹"，更新本月数据
3. 跑上面的"周复盘快照"本月所有
4. 检查 [[30_领域/]] 4 个 MOC，更新"何时更新"段
5. 输出月度报告：
   - 月度 3 件大事
   - 月度 1 个未解决问题
   - 下月 3 个核心动作
```

---

## 8️⃣ 紧急收敛（卡壳时用）

```
我现在卡住了。具体是：{一句话描述}
帮我做 3 件事：
1. 把问题拆成 3 个最小可执行步骤
2. 第一个步骤今天 30 分钟能做完
3. 一旦第一步骤做完，下一步是什么
不要给我方案，只给我"今天 30 分钟内做完"的 1 件事。
```

---

## 9️⃣ 造一条新原子（新）

```
帮我把这条素材拆成 13 库原子：
1. 先看 schema：
   python3 scripts/feishu.py schema 13
2. 准备 data（必填 8 字段）：
   - 原子标题
   - 原子类型（事实/痛点/流程/案例/观点/边界/方案/CTA）
   - 原子内容
   - 来源资料
   - 证据等级（A/B/C/D）
   - Hermes使用状态（可直接取料/需人工复核/仅启发不引用/禁止取料）
   - 适用栏目（5 栏目多选）
   - 适用标签（8 标签多选）
3. dry-run 试一下：
   python3 scripts/feishu.py add 13 --data '{...}' --dry-run
4. 确认后执行：
   python3 scripts/feishu.py add 13 --data '{...}'
5. 关键规则：边界类原子必须填「使用边界」字段
```

---

## 🔟 看选题池进度（新）

```
帮我看选题池进度：
1. 整体分布：
   python3 scripts/feishu.py stats 08
2. 待写列表：
   python3 scripts/feishu.py list 08 --filter "生产状态,==,待写" --limit 20
3. 写作中列表：
   python3 scripts/feishu.py list 08 --filter "生产状态,==,写作中"
4. P0 优先：
   python3 scripts/feishu.py list 08 --filter "优先级,==,P0-先写" --sort 优先级
5. 输出：今日推荐写哪条（按 5 栏目轮转）
```

---

## 1️⃣1️⃣ 发布后回填 09 队列（新）

```
我刚发了 {文章标题}：
1. 在 09 队列加一条：
   python3 scripts/feishu.py add 09 --data '{
     "标题": "...",
     "发布时间": "YYYY-MM-DD HH:MM:SS",
     "阅读": 0,
     "分享": 0,
     "新增关注": 0,
     "关联选题": ["recXXX"]
   }'
2. 把 08 库对应选题标"已发布"：
   python3 scripts/feishu.py update 08 recXXX --field 生产状态 --value "已发布"
3. 把 09 库 record_id 写到 [[50_输出/公众号文章/标题]] 的 frontmatter
```

---

## 1️⃣2️⃣ 整理 Clippings 剪藏（新）

```
帮我整理 [[Clippings/]] 里的剪藏：
1. 扫描 [[Clippings/]] 所有 tag 含 "clippings" 但不含 "archived" 的文件
2. 对每条用 3 问归类：
   - 内容是 [[20_项目/]] 哪个项目的素材？→ 移到项目 + 加归宿标注
   - 是 [[30_领域/]] 哪个领域的补充？→ 移到 MOC 末尾
   - 临时参考？→ 移到 [[40_资源/]] 对应分类
   - 完全没用？→ 删
3. 归档完的加 tag `archived`
4. 输出报告：移到哪里 / 删了什么 / 待重看的有哪些
```

**详细** → [[40_资源/工具收藏/Clippings/MOC]]

---

*最后更新：2026-07-16 · v3（接入 Hermes + 飞书 + Clippings）*
*12 个话术 · 直接 Ctrl+C / Ctrl+V 用*
*所有 `feishu.py` / `hermes.py` 命令来自 [[scripts/]]*
     "阅读": 0,
     "分享": 0,
     "新增关注": 0,
     "关联选题": ["recXXX"]
   }'
2. 把 08 库对应选题标"已发布"：
   python3 scripts/feishu.py update 08 recXXX --field 生产状态 --value "已发布"
3. 把 09 库 record_id 写到 [[50_输出/公众号文章/标题]] 的 frontmatter
```

---

*最后更新：2026-07-16 · v3（接入 Hermes + 飞书接口）*
*11 个话术 · 直接 Ctrl+C / Ctrl+V 用*
*所有 `feishu.py` / `hermes.py` 命令来自 [[scripts/]]*
