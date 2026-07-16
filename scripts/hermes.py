#!/usr/bin/env python3
"""
hermes.py — Hermes 13 步生产 SOP 本地化接口

封装 /tmp/ai-gzh-platform 里的 references 和 scripts，提供：
- hermes.py phases            列出 13 步（每步对应 reference + script）
- hermes.py phase0..8         运行指定 phase
- hermes.py preflight         门禁检查（包装 preflight.py）
- hermes.py postflight --article <md>  8 步质量门禁
- hermes.py check-title --title "..." --digest "..."  字节校验
- hermes.py check-warns --article <md>  检查禁用词
- hermes.py style             写作风格路由（自动判断）
- hermes.py phase1 --topic "..."  从 13 库 + 08 池联动取料

设计原则（师傅 7/16 要求）：
- Hermes 仓库本身在 /tmp/ai-gzh-platform（不重复落地）
- 本地化的只是"调用方式"：phase N → 哪个 reference + 哪个 script
- 一句话能调 13 步中任意一步
"""

from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

# === 配置 ===
HERMES_DIR = Path("/tmp/ai-gzh-platform")
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
SCRIPTS = HERMES_DIR / "scripts"
REFS = HERMES_DIR / "references"

# 13 步 SOP 速查表（来源：SKILL.md 真实结构）
PHASES = [
    ("0", "Preflight", "门禁检查（config/GPT Image 2/飞书/工具依赖）", "preflight.py"),
    ("1", "选题与调研", "爆款调研 + 选题评分 + 风格路由 + 取料（atoms.json）", "assemble_atoms.py"),
    ("2", "内容撰写", "≥2500字 / ≥2表格 / ≥3配图 / 禁用词0", None),
    ("3", "配图生成", "归藏材质插画 + GPT Image 2（最少 4 张）", "generate_image.py"),
    ("4", "HTML 生成", "base64 内嵌，单文件搞定", "build_html.py / md_to_html.py"),
    ("5", "Postflight", "8 步质量门禁", "postflight.py"),
    ("6", "交付", "HTML + 封面，飞书附件", None),
    ("7", "推草稿到公众号", "需 wx-proxy", "push_draft.py"),
    ("8", "多平台分发", "aitoearn MCP + ai-xhs-platform", None),
]

# 风格路由决策表（来源：SKILL.md）
STYLE_ROUTING = [
    ("AI自动化/工作流/内容中台/选题/拆解/改造/实战复盘", "dayao-writing-prompt.md", "5 种文章类型"),
    ("AI工具/课程/变现/n8n/飞书/线索/获客/客服/销售", "n8n-wechat-full-prompt.md", "Writer+Cleaner"),
    ("政策解读/企业深度分析/个人视角叙事", "writing-style.md", "khazix-writer"),
    ("AI企业应用/B端/SaaS/Agent落地/ROI/采购", "writing-style.md + enterprise-windvane.md", "khazix + 企业风向标"),
    ("引流/服务展示/案例引流/帮企业定制/默认", "lead-gen-writing-style.md", "引流文（默认）"),
]

# 写文章时必读 references（按使用频度）
CORE_REFS = {
    "v3 定位 prompt": "dayao-writing-prompt.md",
    "写作风格（实战复盘）": "writing-style.md",
    "写作风格（引流文，默认）": "lead-gen-writing-style.md",
    "n8n 风格": "n8n-wechat-full-prompt.md",
    "小姚 IP 角色": "xiaoyao-ip.md",
    "小姚视觉 DNA": "style-dna.md",
    "标题公式（9 种）": "title-formulas.md",
    "原子化流程": "atomization-pipeline.md",
    "原子化写作 pipeline": "atomized-content-pipeline.md",
    "真实调研方法论": "real-research-methodology.md",
    "QA 清单": "qa-checklist.md",
    "发布前检查清单": "public-release-checklist.md",
    "信息密度规则": "information-density.md",
    "70 条坑（7/11 session）": "pitfalls-session-2026-07-11.md",
    "61 条坑（7/14 session）": "pitfalls-session-2026-07-14.md",
    "系统 prompt 骨架": "system-prompt.md",
    "执行闸门": "execution-gate.md",
    "prompt 模板": "prompt-template.md",
}


def hr(s: str):
    print("─" * 70)
    print(s)
    print("─" * 70)


def cmd_phases(_args):
    hr("Hermes 13 步生产 SOP（来自 SKILL.md 真实结构）")
    for n, name, desc, script in PHASES:
        s = script or "（无专用脚本）"
        print(f"  Phase {n:<2} {name:<14} {desc}")
        print(f"           → {s}")
    print()
    hr("风格路由决策表")
    for kw, files, style in STYLE_ROUTING:
        print(f"  {kw}")
        print(f"    → {files} ({style})")
    print()
    hr("核心 references 速查（写文章时必读）")
    for k, v in CORE_REFS.items():
        print(f"  {k:<24} → {v}")


def _ensure_hermes():
    if not HERMES_DIR.exists():
        print(f"❌ Hermes 仓库不存在：{HERMES_DIR}", file=sys.stderr)
        print(f"   请先：git clone https://github.com/yaoywei/ai-gzh-platform {HERMES_DIR}", file=sys.stderr)
        sys.exit(1)


def _run(cmd: list[str], cwd: Path | None = None):
    """运行 shell 命令并实时输出。"""
    print(f"  $ {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, cwd=cwd or HERMES_DIR)
    return r.returncode


def cmd_phase0(_args):
    _ensure_hermes()
    hr("Phase 0: Preflight 门禁检查")
    return _run(["python3", str(SCRIPTS / "preflight.py")])


def cmd_phase1(args):
    _ensure_hermes()
    hr("Phase 1: 选题 + 取料（联动飞书 13 库 + 08 池）")
    print(f"  Topic: {args.topic or '（未指定，将从 08 库 P0 自动选）'}")
    print(f"  Pool: {args.pool_id or 'recXXXX 自动选'}")
    cmd = ["python3", str(SCRIPTS / "assemble_atoms.py")]
    if args.topic:
        cmd.extend(["--topic", args.topic])
    if args.pool_id:
        cmd.extend(["--pool-id", args.pool_id])
    return _run(cmd)


def cmd_phase3(_args):
    _ensure_hermes()
    hr("Phase 3: 配图（GPT Image 2 + 归藏材质）")
    print("  需要：GPT_IMAGE2_API_KEY 环境变量 + 归藏材质插画 skill")
    print("  见：~/.hermes/skills/guizang-material-illustration/SKILL.md")
    return _run(["python3", str(SCRIPTS / "generate_image.py"), "--help"])


def cmd_phase4(args):
    _ensure_hermes()
    hr("Phase 4: HTML 生成（base64 内嵌）")
    cmd = ["python3", str(SCRIPTS / "build_html.py")]
    if args.article:
        cmd.extend(["--article", args.article])
    if args.imgs:
        cmd.extend(["--imgs-dir", args.imgs])
    return _run(cmd)


def cmd_phase5(args):
    _ensure_hermes()
    hr("Phase 5: Postflight 8 步质量门禁")
    cmd = ["python3", str(SCRIPTS / "postflight.py")]
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    return _run(cmd)


def cmd_phase7(args):
    _ensure_hermes()
    hr("Phase 7: 推草稿到公众号（需 wx-proxy）")
    cmd = ["python3", str(SCRIPTS / "push_draft.py")]
    if args.html:
        cmd.extend(["--html", args.html])
    return _run(cmd)


def cmd_phase8(_args):
    hr("Phase 8: 多平台分发（aitoearn MCP / ai-xhs-platform）")
    print("  需要：aitoearn MCP 已配置 + ai-xhs-platform skill 加载")
    print("  见：SKILL.md Phase 8 段")
    return 0


def cmd_preflight(_args):
    """同 phase 0 便于记忆"""
    return cmd_phase0(_args)


def cmd_postflight(args):
    _ensure_hermes()
    return cmd_phase5(args)


def cmd_check_title(args):
    _ensure_hermes()
    hr("标题 + 摘要字节校验（≤30B / ≤54B）")
    return _run(["python3", str(SCRIPTS / "check_title_digest.py"),
                 "--title", args.title, "--digest", args.digest])


def cmd_check_warns(args):
    """扫描禁用词：赋能/闭环/颠覆式/.../双引号"""
    _ensure_hermes()
    if not args.article:
        print("❌ 需要 --article", file=sys.stderr)
        sys.exit(1)
    FORBIDDEN = ["赋能", "闭环", "颠覆式", "颗粒度", "抓手",
                 "底层逻辑", "综上所述", "值得注意的是",
                 "唯一", "引领", "颠覆"]
    text = Path(args.article).read_text(encoding="utf-8")
    hits = []
    for w in FORBIDDEN:
        n = text.count(w)
        if n:
            hits.append(f"  「{w}」: {n} 次")
    # 双引号
    dq = text.count('"')
    if dq:
        hits.append(f'  双引号 " : {dq} 个（用「」代替）')
    if hits:
        hr("⚠️  禁词命中")
        print("\n".join(hits))
        sys.exit(1)
    else:
        print("✅ 无禁词")


def cmd_style(args):
    """根据师傅输入的关键词，自动判断写作风格"""
    hr("风格路由判断（输入关键词：" + (args.keyword or "默认") + "）")
    keyword = (args.keyword or "").lower()
    for kw, files, style in STYLE_ROUTING:
        for k in kw.split("/"):
            if k and k in keyword:
                print(f"✅ 匹配：{kw}")
                print(f"   → 风格：{style}")
                print(f"   → 文件：{files}")
                ref = REFS / files.split(" + ")[0].strip()
                if ref.exists():
                    print(f"   → 完整路径：{ref}")
                return 0
    # 默认：引流文
    kw, files, style = STYLE_ROUTING[-1]
    print(f"⚡ 未匹配到明确风格，使用默认：{kw}")
    print(f"   → 风格：{style}")
    print(f"   → 文件：{files}")
    ref = REFS / files.strip()
    if ref.exists():
        print(f"   → 完整路径：{ref}")
    return 0


def cmd_read_ref(args):
    """打印某个 reference 的内容（带行号）"""
    _ensure_hermes()
    ref = REFS / args.file
    if not ref.exists():
        # 模糊匹
        candidates = list(REFS.glob(f"*{args.file}*"))
        if candidates:
            ref = candidates[0]
            print(f"（模糊匹配：{ref.name}）")
        else:
            print(f"❌ 找不到 {args.file}", file=sys.stderr)
            sys.exit(1)
    print(f"📖 {ref}\n")
    print(ref.read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes 13 步生产 SOP 本地化接口",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("phases", help="列出 13 步 + 风格路由 + 核心 references").set_defaults(fn=cmd_phases)

    sp = sub.add_parser("preflight", help="Phase 0 门禁")
    sp.set_defaults(fn=cmd_preflight)

    sp = sub.add_parser("phase1", help="Phase 1 选题 + 取料（联动飞书）")
    sp.add_argument("--topic", help="关键词")
    sp.add_argument("--pool-id", help="08 库 record_id")
    sp.set_defaults(fn=cmd_phase1)

    sp = sub.add_parser("phase3", help="Phase 3 配图")
    sp.set_defaults(fn=cmd_phase3)

    sp = sub.add_parser("phase4", help="Phase 4 HTML 生成")
    sp.add_argument("--article", help="article.md 路径")
    sp.add_argument("--imgs", help="imgs/ 目录")
    sp.set_defaults(fn=cmd_phase4)

    sp = sub.add_parser("postflight", help="Phase 5 质量门禁")
    sp.add_argument("--output-dir", help="输出目录")
    sp.set_defaults(fn=cmd_postflight)

    sp = sub.add_parser("phase7", help="Phase 7 推草稿")
    sp.add_argument("--html", help="HTML 文件路径")
    sp.set_defaults(fn=cmd_phase7)

    sub.add_parser("phase8", help="Phase 8 多平台分发").set_defaults(fn=cmd_phase8)

    sp = sub.add_parser("check-title", help="标题+摘要字节校验")
    sp.add_argument("--title", required=True)
    sp.add_argument("--digest", required=True)
    sp.set_defaults(fn=cmd_check_title)

    sp = sub.add_parser("check-warns", help="扫描禁用词")
    sp.add_argument("--article", help="article.md 路径")
    sp.set_defaults(fn=cmd_check_warns)

    sp = sub.add_parser("style", help="按关键词判断写作风格")
    sp.add_argument("--keyword", help="师傅输入的关键词，留空 = 默认引流文")
    sp.set_defaults(fn=cmd_style)

    sp = sub.add_parser("read-ref", help="读取某 reference 内容")
    sp.add_argument("file", help="reference 文件名或关键词")
    sp.set_defaults(fn=cmd_read_ref)

    args = p.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
