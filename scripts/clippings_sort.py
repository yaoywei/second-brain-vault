#!/usr/bin/env python3
"""
clippings_sort.py — 扫描 Clippings/ 下未归档的剪藏，提议归宿

用法：
  python3 scripts/clippings_sort.py           列出待归档的文件 + 提议
  python3 scripts/clippings_sort.py --apply  自动归档（按 frontmatter 里的 tags 字段）
  python3 scripts/clippings_sort.py --tag "archive"  给所有未归档文件加 archived tag

设计原则：
- 不删任何文件（除非师傅显式说删）
- 默认提议归宿，师傅 ✅/❌ 后再 apply
- 输出格式跟 [[90_模板/Claudian话术包#1️⃣ 清空收件箱]] 兼容
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
CLIPPINGS_DIR = VAULT_ROOT / "Clippings"
MOC_LINK = "[[40_资源/工具收藏/Clippings/MOC]]"


def scan_unarchived() -> list[Path]:
    """扫 Clippings/ 下所有 .md 文件，找 tag 含 'clippings' 但不含 'archived' 的"""
    if not CLIPPINGS_DIR.exists():
        return []
    result = []
    for f in CLIPPINGS_DIR.rglob("*.md"):
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        # 看 frontmatter 里的 tags
        m = re.search(r"^tags:\s*\n((?:\s+-\s+.+\n)+)", text, re.MULTILINE)
        if not m:
            # 没 frontmatter tags 也算"未归档"
            result.append(f)
            continue
        tag_block = m.group(1)
        if "archived" in tag_block:
            continue
        if "clippings" not in tag_block:
            continue
        result.append(f)
    return result


def propose_destination(file: Path) -> str:
    """根据 frontmatter 的 source + description 提议归宿。极简版——返回原文摘要。"""
    text = file.read_text(encoding="utf-8")
    # 提取 description
    desc_m = re.search(r"^description:\s*\"?(.+?)\"?$", text, re.MULTILINE)
    desc = desc_m.group(1) if desc_m else ""
    # 提取 source
    src_m = re.search(r"^source:\s*\"?(.+?)\"?$", text, re.MULTILINE)
    src = src_m.group(1) if src_m else ""
    # 提取 title
    title_m = re.search(r"^title:\s*\"?(.+?)\"?$", text, re.MULTILINE)
    title = title_m.group(1) if title_m else file.stem
    return f"📄 {file.name}\n   标题: {title}\n   描述: {desc[:100]}{'...' if len(desc) > 100 else ''}\n   来源: {src}\n"


def cmd_list(_args):
    """列出待归档的文件 + 提议。"""
    files = scan_unarchived()
    if not files:
        print("✅ Clippings/ 已全部归档（或为空）")
        return
    print(f"📥 待归档剪藏 {len(files)} 条：\n")
    for f in files:
        print(propose_destination(f))
        print("  → 待你判断：项目 / 领域 / 资源 / 删")
        print("-" * 60)
    print(f"\n详细归档指南 → {MOC_LINK}")


def cmd_apply(_args):
    """按 frontmatter 里的 tags 字段自动归档。"""
    files = scan_unarchived()
    if not files:
        print("✅ 没有待归档的剪藏")
        return
    print(f"⏳ 自动归档 {len(files)} 条...")
    for f in files:
        text = f.read_text(encoding="utf-8")
        # 给 frontmatter 加 archived tag
        m = re.search(r"^(tags:\s*\n)((?:\s+-\s+.+\n)+)", text, re.MULTILINE)
        if m:
            new_tags = m.group(2) + "  - archived\n"
            new_text = text[:m.start()] + m.group(1) + new_tags + text[m.end():]
        else:
            # 没 tags 字段，添加
            new_text = re.sub(
                r"^(---.*?---\n)",
                r"\1tags:\n  - archived\n",
                text,
                count=1,
                flags=re.DOTALL,
            )
        f.write_text(new_text, encoding="utf-8")
        print(f"  ✅ {f.name} → 加 archived tag")
    print(f"\n归档完成。详细 → {MOC_LINK}")


def cmd_tag(args):
    """给文件加自定义 tag（默认 archived）。"""
    tag = args.tag
    files = scan_unarchived()
    if not files:
        print("✅ 没有待归档的剪藏")
        return
    for f in files:
        text = f.read_text(encoding="utf-8")
        m = re.search(r"^(tags:\s*\n)((?:\s+-\s+.+\n)+)", text, re.MULTILINE)
        if m:
            new_tags = m.group(2) + f"  - {tag}\n"
            new_text = text[:m.start()] + m.group(1) + new_tags + text[m.end():]
        else:
            new_text = re.sub(
                r"^(---.*?---\n)",
                rf"\1tags:\n  - {tag}\n",
                text,
                count=1,
                flags=re.DOTALL,
            )
        f.write_text(new_text, encoding="utf-8")
        print(f"  ✅ {f.name} → 加 {tag} tag")


def main():
    p = argparse.ArgumentParser(
        prog="clippings_sort",
        description="扫描 Clippings/ 剪藏，提议归宿或自动归档",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="列出待归档的文件").set_defaults(fn=cmd_list)
    sub.add_parser("apply", help="自动归档（加 archived tag）").set_defaults(fn=cmd_apply)

    sp = sub.add_parser("tag", help="给所有未归档文件加 tag")
    sp.add_argument("tag", help="要加的 tag 名")
    sp.set_defaults(fn=cmd_tag)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
