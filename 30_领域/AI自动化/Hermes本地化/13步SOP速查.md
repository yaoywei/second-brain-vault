---
type: knowledge
area: AI自动化
created: 2026-07-16
updated: 2026-07-16-v3
status: active
tags: [Hermes, SOP, 13步, 本地化, 公众号]
related: [[30_领域/AI自动化/Hermes技能自检]], [[30_领域/AI自动化/Hermes本地化/接口速查]], [[scripts/hermes.py]]
---

# 🚀 Hermes 13 步生产 SOP（速查表）

> **本地化方式**：仓库在 `/tmp/ai-gzh-platform`，调用方式装在 `[[scripts/hermes.py]]`。
> **原则**：仓库本身不重复落地，**只本地化调用方式 + 速查索引**。

---

## 🎯 13 步（按顺序）

| Phase | 名称 | 作用 | 调什么 | 师傅做什么 |
|-------|------|------|--------|-----------|
| **0** | Preflight | 门禁检查 | `hermes.py preflight` 或 `phase0` | 看绿/红 |
| **1** | 选题 + 取料 | 爆款调研 + 风格路由 + 联动飞书 13 库 | `hermes.py phase1 --topic "..."` 或 `phase1 --pool-id recXXXX` | 选一条 08 库 P0 选题 |
| **2** | 内容撰写 | 按风格写 ≥2500字 | `hermes.py style --keyword "..."` | AI 起草，人工审 |
| **3** | 配图 | 归藏材质 + GPT Image 2 | `hermes.py phase3` | 跑配图，校验 |
| **4** | HTML 生成 | base64 内嵌 | `hermes.py phase4 --article x.md --imgs imgs/` | 跑 build_html.py |
| **5** | Postflight | 8 步质量门禁 | `hermes.py postflight --output-dir xxx` | 看红就改 |
| **6** | 交付 | HTML + 封面 | 飞书附件发送 | 推给师傅审 |
| **7** | 推草稿 | 推微信草稿箱 | `hermes.py phase7 --html x.html` | （需 wx-proxy）|
| **8** | 多平台分发 | 公众号 → 小红书/知乎/抖音 | `hermes.py phase8` | （需 aitoearn MCP）|

---

## 🎨 风格路由（写之前先判断）

> ⚠️ **默认是引流文**（7/14 师傅纠正过一次）

| 关键词 / 场景 | 风格 | 调什么 reference |
|--------------|------|-----------------|
| AI 自动化 / 工作流 / 内容中台 / 选题 / 拆解 / 改造 / 实战复盘 | **5 种文章类型** | `dayao-writing-prompt.md` |
| AI 工具 / 课程 / 变现 / n8n / 飞书 / 线索 / 获客 / 客服 / 销售 | **Writer+Cleaner** | `n8n-wechat-full-prompt.md` |
| 政策解读 / 企业深度分析 / 个人视角 | **khazix-writer** | `writing-style.md` |
| AI 企业应用 / B 端 / SaaS / Agent 落地 / ROI | **khazix + 企业风向标** | `writing-style.md` + `enterprise-windvane.md` |
| 引流 / 展示服务 / 案例引流 / **默认** | **引流文** | `lead-gen-writing-style.md` |

**自动判断**：`hermes.py style --keyword "工作流拆解"` → 给出风格 + 完整路径。

---

## ✅ 师傅一句话走通（一行命令）

```bash
# 完整流程
hermes.py preflight && \
hermes.py phase1 --pool-id recXXXX && \
hermes.py style --keyword "工作流拆解" && \
hermes.py phase3 && \
hermes.py phase4 --article article.md --imgs imgs/ && \
hermes.py postflight --output-dir output/ && \
hermes.py check-warns --article article.md
```

---

## 📚 写文章时必读 references（按使用频度）

| 用途 | 文件 | 必读度 |
|------|------|--------|
| v3 定位 + Writer/Cleaner prompt | `dayao-writing-prompt.md` | ⭐⭐⭐ |
| 引流文（默认） | `lead-gen-writing-style.md` | ⭐⭐⭐ |
| 标题公式（9 种）| `title-formulas.md` | ⭐⭐⭐ |
| 70 条坑（7/11）| `pitfalls-session-2026-07-11.md` | ⭐⭐⭐ |
| 61 条坑（7/14）| `pitfalls-session-2026-07-14.md` | ⭐⭐⭐ |
| 原子化流程 | `atomization-pipeline.md` | ⭐⭐ |
| 真实调研方法论 | `real-research-methodology.md` | ⭐⭐ |
| 小姚 IP 角色 | `xiaoyao-ip.md` | ⭐⭐ |
| 小姚视觉 DNA | `style-dna.md` | ⭐⭐ |
| QA 清单 | `qa-checklist.md` | ⭐⭐ |
| 发布前检查清单 | `public-release-checklist.md` | ⭐⭐ |
| 信息密度规则 | `information-density.md` | ⭐ |
| 系统 prompt 骨架 | `system-prompt.md` | ⭐ |
| 执行闸门 | `execution-gate.md` | ⭐ |
| prompt 模板 | `prompt-template.md` | ⭐ |

**完整路径**：`/tmp/ai-gzh-platform/references/`

**一次性打印**：`hermes.py phases`

---

## 🛠 联动飞书的 3 个关键点

| 联动 | 工具 | 命令 |
|------|------|------|
| 13 库按栏目过滤 | `[[scripts/feishu.py]]` | `feishu.py list 13 --filter "适用栏目,intersects,工作流拆解"` |
| 08 库 P0 选题 | `feishu.py` | `feishu.py list 08 --filter "优先级,==,P0-先写"` |
| 08 库生产状态 | `feishu.py` | `feishu.py stats 08`（看「待写 vs 写作中 vs 已发」） |

---

## 🚨 5 大硬约束（写之前必过）

1. **≥2500 字**
2. **≥2 个表格**
3. **≥3 个配图标记**（`【配图X：描述】`）
4. **禁用词 0 命中**（赋能/闭环/颠覆式/.../双引号"）
5. **数据全部来自 atoms.json**（不编造）

**自动校验**：
- 字数/表格/配图：`hermes.py postflight`
- 禁用词：`hermes.py check-warns --article article.md`
- 标题/摘要字节：`hermes.py check-title --title "..." --digest "..."`

---

*最后更新：2026-07-16 · v3*
*设计原则：仓库在 /tmp/ai-gzh-platform，vault 只装调用方式*
