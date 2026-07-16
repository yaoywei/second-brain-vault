#!/usr/bin/env python3
"""
article_to_html.py — article.md + imgs/ → 公众号 base64 内嵌 HTML

特性：
- 自动去掉 frontmatter / 内部元信息
- 4 张图 base64 内嵌，1 个 HTML 文件搞定
- 鲲鹏蓝排版（蓝 #002FA7 + 灰 + 黑线）
- 适配手机阅读（行高 1.8、段间空行、段落 ≤ 4 行）

用法：
  python3 article_to_html.py --article 50_输出/公众号文章/2026-07-16-Hermes取料规则.md
"""

from __future__ import annotations
import argparse
import base64
import io
import re
import sys
from pathlib import Path

# === 配置 ===
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
DEFAULT_IMGS_DIR = VAULT_ROOT / "50_输出" / "公众号文章" / "imgs"

# 鲲鹏蓝（IKB Blue）
COLOR_PRIMARY = "#002FA7"
COLOR_BG = "#FFFFFF"
TEXT = "#1F2937"
SUB = "#6B7280"
BORDER = "#E5E7EB"
SOFT_BG = "#F8FAFC"


def img_to_base64(png_path: Path) -> str:
    """PNG → base64。保留 PNG 透明（如有）。"""
    raw = png_path.read_bytes()
    return base64.b64encode(raw).decode()


def find_image_by_index(imgs_dir: Path, idx: int) -> Path | None:
    """按编号找：配图1 / 配图-1 / img-1 / 配图1_xxx.png 都行。"""
    for f in sorted(imgs_dir.iterdir()):
        if not f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            continue
        # 配图1 / 配图-1 / 配图1_xxx.png（数字后允许 - _ 空格 或 直接到结尾）
        if re.search(rf"配图[-_ ]?{idx}(?:[-_ ]|$)", f.name) or re.search(rf"img[-_ ]?{idx}(?:[-_ ]|$)", f.name):
            return f
    return None


def strip_metadata(text: str) -> str:
    """去掉 frontmatter（--- 之间的 YAML）+ footer（从 *Draft v* 开始）+ related 行"""
    # 1. 去掉 frontmatter（只切开头的两个 ---，后面的水平线不动）
    # frontmatter 格式：开头是 ---，第二行开始是 YAML，遇到下一个 --- 结束
    m = re.match(r"^---\s*\n(.+?)\n---\s*\n?", text, re.DOTALL)
    if m:
        text = text[m.end():]
    # 2. 去掉 footer（*Draft v* 之后到文末）
    text = re.split(r"^\*Draft v", text, maxsplit=1, flags=re.MULTILINE)[0]
    # 3. 去掉开头的 related: 行残留
    text = re.sub(r"^related:.*$", "", text, flags=re.MULTILINE)
    return text.strip()


def replace_image_markers(text: str, imgs_dir: Path) -> str:
    """把【配图X：描述】替换成 base64 内嵌的 <img>"""
    def _r(m: re.Match) -> str:
        idx = int(m.group(1))
        img = find_image_by_index(imgs_dir, idx)
        if not img:
            return f'<p style="color:#999;">[配图{idx} 未找到]</p>'
        b64 = img_to_base64(img)
        return f'<p style="margin:32px 0;text-align:center;"><img src="data:image/png;base64,{b64}" alt="配图{idx}" style="max-width:100%;border-radius:8px;display:inline-block;box-shadow:0 2px 8px rgba(0,0,0,0.08);"></p>'
    return re.sub(r"【配图(\d+)[：:][^】]*】", _r, text)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_inline(text: str) -> str:
    text = escape_html(text)
    # **xxx** → <strong>
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        f'<strong style="color:{TEXT};font-weight:600;">\\1</strong>',
        text,
    )
    # `xxx` → <code>
    text = re.sub(
        r"`([^`]+)`",
        f'<code style="background:{SOFT_BG};padding:1px 6px;border-radius:4px;font-family:Menlo,Consolas,monospace;font-size:14px;color:{COLOR_PRIMARY};">\\1</code>',
        text,
    )
    return text


def is_table_sep(row: str) -> bool:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return all(re.match(r"^:?-+:?$", c) for c in cells if c)


def render_table(rows: list[str]) -> str:
    rows = [r for r in rows if not is_table_sep(r)]
    if not rows:
        return ""
    out = [
        f'<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:15px;line-height:1.6;background:#FFFFFF;border:1px solid {BORDER};border-radius:6px;overflow:hidden;">'
    ]
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        tag = "th" if i == 0 else "td"
        if i == 0:
            style = f"background:{COLOR_PRIMARY}10;color:{COLOR_PRIMARY};font-weight:600;text-align:left;padding:10px 12px;border-bottom:1px solid {BORDER};"
        else:
            style = f"padding:10px 12px;border-bottom:1px solid #F3F4F6;color:{TEXT};"
            if i % 2 == 0:
                style += "background:#F9FAFB;"
        row_html = "".join(f'<{tag} style="{style}">{render_inline(c)}</{tag}>' for c in cells)
        out.append(f"<tr>{row_html}</tr>")
    out.append("</table>")
    return "\n".join(out)


def render_quote(text: str) -> str:
    return (
        f'<blockquote style="margin:20px 0;padding:12px 16px;background:{COLOR_PRIMARY}08;'
        f'border-left:3px solid {COLOR_PRIMARY};color:{COLOR_PRIMARY};'
        f'font-size:15px;line-height:1.7;border-radius:0 6px 6px 0;">'
        f"{render_inline(text)}</blockquote>"
    )


def render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    style = "list-style:none;padding-left:0;margin:16px 0;"
    item_style = f"padding:6px 0 6px 24px;position:relative;color:{TEXT};font-size:15px;line-height:1.75;"
    out = [f'<{tag} style="{style}">']
    for i, item in enumerate(items, 1):
        if ordered:
            out.append(
                f'<li style="{item_style}">'
                f'<span style="position:absolute;left:6px;color:{COLOR_PRIMARY};font-weight:600;">{i}.</span>'
                f"{render_inline(item)}</li>"
            )
        else:
            out.append(
                f'<li style="{item_style}">'
                f'<span style="position:absolute;left:6px;top:14px;width:6px;height:6px;background:{COLOR_PRIMARY};border-radius:50%;"></span>'
                f"{render_inline(item)}</li>"
            )
    out.append(f"</{tag}>")
    return "\n".join(out)


def render_h(text: str, level: int) -> str:
    sizes = {1: 24, 2: 20, 3: 17, 4: 16}
    s = sizes.get(level, 16)
    pad_top = 32 if level == 1 else 24
    return f'<h{level} style="font-size:{s}px;font-weight:700;color:{TEXT};line-height:1.4;margin:{pad_top}px 0 12px;">{render_inline(text)}</h{level}>'


def render_p(text: str) -> str:
    if not text.strip():
        return ""
    return f'<p style="font-size:16px;line-height:1.8;color:{TEXT};margin:14px 0;">{render_inline(text)}</p>'


def md_to_html(body: str) -> str:
    """极简 Markdown 渲染（够用，不支持嵌套列表/代码块）"""
    lines = body.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 跳过空行
        if not line.strip():
            i += 1
            continue
        # 水平线
        if re.match(r"^-{3,}$", line.strip()):
            out.append(f'<hr style="border:0;border-top:1px solid {BORDER};margin:24px 0;">')
            i += 1
            continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            out.append(render_h(m.group(2).strip(), len(m.group(1))))
            i += 1
            continue
        # 引用（可多行）
        if line.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(lines[i].lstrip(">").strip())
                i += 1
            out.append(render_quote("\n".join(quote_lines)))
            continue
        # 表格（连续多行 | 开头）
        if line.strip().startswith("|") and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            table_rows = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_rows.append(lines[i])
                i += 1
            out.append(render_table(table_rows))
            continue
        # 有序列表
        if re.match(r"^\d+\.\s+", line.strip()):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append(render_list(items, ordered=True))
            continue
        # 无序列表
        if re.match(r"^[-*]\s+", line.strip()):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append(render_list(items, ordered=False))
            continue
        # 默认段落
        out.append(render_p(line))
        i += 1
    return "\n".join(out)


def render_article_html(article_md: str, imgs_dir: Path) -> str:
    body = strip_metadata(article_md)
    # 取第一个 # 标题
    title_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_m.group(1) if title_m else "公众号文章"
    # 去掉第一个 # 标题（HTML 单独渲染）
    body = re.sub(r"^#\s+.+?\n", "", body, count=1, flags=re.MULTILINE).strip()
    # 关键：先用占位符替换配图 marker（避免被 md_to_html escape）
    img_placeholders: list[str] = []  # 存真实 HTML
    def _placeholder(m: re.Match) -> str:
        idx = int(m.group(1))
        img = find_image_by_index(imgs_dir, idx)
        if not img:
            return f'<p style="color:#999;">[配图{idx} 未找到]</p>'
        b64 = img_to_base64(img)
        html = f'<p style="margin:32px 0;text-align:center;"><img src="data:image/png;base64,{b64}" alt="配图{idx}" style="max-width:100%;border-radius:8px;display:inline-block;box-shadow:0 2px 8px rgba(0,0,0,0.08);"></p>'
        img_placeholders.append(html)
        return f"\n@@IMG_PLACEHOLDER_{len(img_placeholders)-1}@@\n"
    body = re.sub(r"【配图(\d+)[：:][^】]*】", _placeholder, body)
    # Markdown → HTML
    body_html = md_to_html(body)
    # 把占位符替换回真实 HTML
    for i, html in enumerate(img_placeholders):
        body_html = body_html.replace(f"@@IMG_PLACEHOLDER_{i}@@", html)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(title)}</title>
</head>
<body style="margin:0;padding:24px 20px;background:#F5F5F5;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;">
<div style="max-width:720px;margin:0 auto;background:#FFFFFF;padding:32px 24px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
<h1 style="font-size:26px;font-weight:700;color:{TEXT};line-height:1.4;margin:0 0 8px;">{escape_html(title)}</h1>
<p style="color:{SUB};font-size:13px;margin:0 0 24px;">大姚｜AI 自动化工作流实战</p>
{body_html}
<hr style="border:0;border-top:1px solid {BORDER};margin:32px 0 16px;">
<p style="text-align:center;color:{SUB};font-size:13px;margin:0;">👆 回复「6 步」领取 6 步公众号自动化 SOP</p>
</div>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(
        prog="article_to_html",
        description="article.md + imgs/ → 公众号 base64 内嵌 HTML",
    )
    p.add_argument("--article", required=True, help="article.md 路径")
    p.add_argument("--imgs-dir", default=str(DEFAULT_IMGS_DIR), help=f"图片目录（默认 {DEFAULT_IMGS_DIR}）")
    p.add_argument("--out", help="输出 HTML 路径（默认同名 .html）")
    args = p.parse_args()

    article_path = Path(args.article)
    if not article_path.exists():
        # 试相对 vault
        alt = VAULT_ROOT / args.article
        if alt.exists():
            article_path = alt
        else:
            print(f"❌ 找不到 {args.article}", file=sys.stderr)
            sys.exit(1)

    imgs_dir = Path(args.imgs_dir)
    out_path = Path(args.out) if args.out else article_path.with_suffix(".html")

    text = article_path.read_text(encoding="utf-8")
    html = render_article_html(text, imgs_dir)
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ 已生成：{out_path}")
    print(f"   大小：{out_path.stat().st_size // 1024} KB")
    print(f"   配图目录：{imgs_dir}")


if __name__ == "__main__":
    main()
