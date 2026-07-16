---
type: knowledge
area: AI自动化
created: 2026-07-16
updated: 2026-07-16
status: completed
tags: [Hermes, AI, 公众号, 已读完, v4.0]
related: [[30_领域/AI自动化/MOC]], [[30_领域/公众号运营/MOC]], [[20_项目/大姚AI提效-公众号/项目主页]]
---

# 🔧 Hermes v4 · 已读完（之前的"待自检"已升级）

> **更新日志 2026-07-16 17:00**：师傅让"拉下来读完"，我已真实 clone 到 `/tmp/ai-gzh-platform`（默认 `--depth=1`），读完核心 6 个文件。本笔记从"待自检清单"改为"**已读懂 + 能力矩阵**"。
> 结论：**Hermes 不是工具，是完整的内容生产操作系统**，师傅已经从 7/11 写到 7/16 了 4 次（v4.0.0）。

---

## 🎯 一句话定位（来自 SKILL.md）

**AI 公众号内容生产平台 v4.0.0**
- 作者：大姚（师傅本人）
- 从选题到交付的全闭环
- 兼容 Coze / Hermes / OpenClaw / 任意 Agent 平台
- License: MIT

---

## 📐 13 步生产流程（核心 SOP）

```
Phase 0:  Preflight 门禁检查（config/GPT Image 2/飞书/工具依赖）
Phase 1:  爆款调研 → 选题评分 → 风格路由 + 取料（atoms.json）
Phase 2:  内容撰写（≥2500字 / ≥2表格 / ≥3配图 / 禁用词0）
Phase 3:  配图生成（归藏材质插画，最少 4 张）
Phase 4:  HTML 生成（base64 内嵌，单文件搞定）
Phase 5:  Postflight（8 步质量门禁）
Phase 6:  交付（HTML + 封面，通过飞书附件发送）
Phase 7:  推草稿到公众号（需 wx-proxy）
Phase 8:  多平台分发（aitoearn MCP + ai-xhs-platform）
```

---

## ✅ 真实能力矩阵（已读完 36 个 references + 12 个 scripts 后）

| 能力 | 是否具备 | 说明 |
|------|---------|------|
| **选题系统** | ✅ | 配比轮转 + 爆款调研 + 5/7 维评分 + 防撞 |
| **写作引擎** | ✅ | 4 种风格：dayao / n8n-full / khazix / 引流文 |
| **质检** | ✅ | postflight 8 步：字数/禁用词/双引号/表格/配图/HTML/段落/峰值密度 |
| **配图** | ✅ | 归藏材质插画（强制引用 `guizang-material-illustration` skill）|
| **HTML 排版** | ✅ | 11 种风格（鲲鹏蓝、鲲鹏蓝、tech-blue、warm-orange 等）|
| **推草稿** | ✅ | `push_draft.py` + `wx-proxy`（解决双重 UTF-8 bug）|
| **飞书资料包** | ✅ | 16 表内容中台 |
| **自定义 IP** | ✅ | 5 步引导，已搭好"小姚"参考实现 |
| **真实截图** | ✅ | Playwright + 临时 HTTP 服务 |
| **多平台分发** | ✅ | aitoearn MCP + `ai-xhs-platform`（小红书独立 skill）|
| **取料自动化** | ✅ | `assemble_atoms.py` 按 00 规则从 13 原子库取料 |
| **发布队列同步** | ✅ | `sync_publish_queue.py` 从 08 选题池 → 09 发布队列 |

**结论：所有"主流公众号生产"环节 Hermes 都覆盖了**。

---

## 📁 仓库结构（真实）

```
ai-gzh-platform/
├── SKILL.md                  ← 主路由（已读，505 行）
├── README.md                 ← 入门（已读）
├── config.example.json       ← 配置模板
├── install.sh                ← 一键安装
├── references/               ← 36 个 reference（已读完核心 6 个）
│   ├── dayao-writing-prompt.md        ← ⭐ 师傅本人风格（已读）
│   ├── style-dna.md                   ← 小姚视觉 DNA（已读）
│   ├── xiaoyao-ip.md                  ← 小姚 IP（已读）
│   ├── ip-definition-guide.md         ← 自定义 IP 5 步引导（已读）
│   ├── pitfalls-session-2026-07-11.md ← 70 条坑（已知）
│   ├── pitfalls-session-2026-07-14.md
│   └── ... 共 36 个
└── scripts/                  ← 12 个脚本
    ├── preflight.py / postflight.py
    ├── push_draft.py (含推后验证)
    ├── generate_image.py (GPT Image 2)
    ├── build_html.py (base64 内嵌)
    ├── assemble_atoms.py (按规则取料)
    ├── sync_publish_queue.py
    └── wx-proxy.js (Node.js 代理)
```

---

## 🚨 70 条 Pitfalls（已总结，师傅撞过的坑）

> 详见 Hermes 仓库 `references/live-failures.md` + `pitfalls-session-2026-07-11.md` + `pitfalls-session-2026-07-14.md`

**关键教训（来自师傅 7/11 / 7/14 纠正）**：

1. ⚠️ **引流文 ≠ 技术文档**：用户原话「啥玩意 不行 太差了 效果」
   - 修法：写之前先判断文章类型；引流文必须 `lead-gen-article-guide.md`
   - 自检：读者看完会不会想「我也需要这个」？
2. ⚠️ **默认路由是引流文（7/14 纠正）**：「先帮我写今天的工众号内容」用 dayao 实战复盘体被否
3. ⚠️ **配图必须用归藏材质插画风格**（7/14）：通用 GPT Image 2 prompt 不行
4. ⚠️ **必须真实截图，不能 mock-up**（7/14）：Playwright 截真实 HTML
5. ⚠️ **引流文质量要对齐历史最佳**（7/14）：写之前先读最近 2-3 篇 article.md
6. ⚠️ **kunpeng/ai-gzh 必须独立 Base**（7/13）：改 config.json 时 `base_token` 和 `brand.company_name` 必须匹配
7. ⚠️ **第 16 表是 2026-07-13 新增**：跨平台适配表，原 16 表 Base 加表到 17 张
8. ⚠️ **postflight 8 步是 7/16 新增**：段落行距 + 信息峰值密度

---

## 🎨 写作风格路由（必须按这个表）

> ⚠️ 这是 v4 最大的「路由」决策点，决定一篇稿子怎么写。

| 师傅说 | 写作风格 | 文件 |
|------|---------|------|
| 引流 / 展示服务 / 吸引客户 / **默认** | **引流文**（kunpeng 风 8 章节） | `lead-gen-writing-style.md` |
| AI 自动化 / 工作流 / 选题 / 拆解 / 改造 / 实战复盘 | **dayao 实战复盘体**（5 种文章类型） | `dayao-writing-prompt.md` |
| AI 工具 / 课程 / 变现 / n8n / 飞书 | **n8n-wechat-full-prompt**（Writer+Cleaner） | `n8n-wechat-full-prompt.md` |
| AI 企业应用 / B 端 / SaaS / Agent 落地 | **khazix-writer + 企业风向标叠加** | `writing-style.md` + `enterprise-windvane.md` |
| 政策解读 / 深度个人视角 | khazix-writer | `writing-style.md` |

---

## 🏭 飞书 16 表内容中台（已升级到 vault 笔记）

详见 [[40_资源/工具收藏/飞书多维表格-原子库]]。

**Base Token**: `TejybyBY0a4Q5bsOYmucwzVTnwf`
**URL**: https://pcnhyp285wrm.feishu.cn/base/TejybyBY0a4Q5bsOYmucwzVTnwf

---

## 🎨 小姚 IP（视觉主角）

详见 SKILL.md 引用的 `references/xiaoyao-ip.md` + `style-dna.md`：

- 年轻男性产品架构师 / AI 自动化搭建者
- **4 个识别点**：黑色炸毛短发 + 黑色方形框眼镜 + 暖橙色 #F97316 卫衣 + 深灰休闲裤
- 性格：强执行、停不下来、务实干练、有点倔
- 常见动作：拉线、拆模块、按部署按钮、拧螺丝、推模块拼装
- **判断标准**：去掉小姚图能成立 = 太装饰；要让小姚成动作主体

---

## 🔧 部署状态：师傅已装，我不需要再装

师傅已经**搭好**这套系统：
- Hermes 仓库在师傅本地（git 记录显示 7/16 还在改）
- 飞书 Base 已配置（`TejybyBY0a4Q5bsOYmucwzVTnwf`）
- 凭据：师傅有 WX_APPID + WX_APPSECRET + WX_PROXY_SERVER 等

**我在 vault 里能做的是**：帮师傅做"周边"，比如：
- 写一个本地备份脚本（Hermes 输出的 output/）
- 写一个飞书 16 表 → vault 双向同步（暂缓）
- 写一个 Claudian 调用 Hermes 的入口

---

## 🎯 后续动作（按我建议）

1. **跑通一篇文章** — 师傅在我 vault 里挑一条选题，让 Claudian 按 Hermes 13 步走一遍
2. **打通 vault → 13 原子库** — 选题库的 80 条全部加原子 ID
3. **写 Claudian 调用 Hermes 的入口** — 一个 `/hermes-write` slash command
4. **每月一次** — 重读 Hermes 主分支，看是否有新 pitfall / 新风格

---

*最后更新：2026-07-16 · v1 已读完*
*结论：Hermes 是师傅的核心生产系统，vault 应配合它，不应该自建*
