#!/usr/bin/env python3
"""
image_gen.py — 中转站生图本地化接口

封装 https://api.zhongzhuan.chat + 配图 skill
- image_gen.py gen --prompt "..." --out x.png [--size 1024x1024] [--model gpt-image-2-c]
- image_gen.py config                     显示当前配置
- image_gen.py styles                    列出归藏材质配图风格

⚠️ 成本：
- gpt-image-2-c: ~¥0.10-0.30/张（1024x1024）
- 1 篇公众号 4 张配图 ≈ ¥0.5-1.2
- 月预算由师傅控制（暂设 ¥50/月）
"""

from __future__ import annotations
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

# === 配置（API key 走 ~/.config/second-brain/，不进 vault）===
API_KEY_PATH = Path.home() / ".config" / "second-brain" / "image_gen.env"
API_BASE = "https://api.zhongzhuan.chat"
DEFAULT_MODEL = "gpt-image-2-c"
DEFAULT_SIZE = "1024x1024"
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
SKILL_DIR = Path("/tmp/guizang-material-illustration")
DEFAULT_OUTPUT = VAULT_ROOT / "50_输出" / "公众号文章" / "imgs"


def _load_key() -> str:
    """从 ~/.config/second-brain/image_gen.env 读 IMAGE_GEN_API_KEY。"""
    if not API_KEY_PATH.exists():
        print(f"❌ 找不到 {API_KEY_PATH}", file=sys.stderr)
        print(f"   请创建：echo 'IMAGE_GEN_API_KEY=sk-xxx' > {API_KEY_PATH} && chmod 600 {API_KEY_PATH}", file=sys.stderr)
        sys.exit(1)
    for line in API_KEY_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "IMAGE_GEN_API_KEY":
                return v.strip()
    print(f"❌ {API_KEY_PATH} 里没找到 IMAGE_GEN_API_KEY", file=sys.stderr)
    sys.exit(1)


def cmd_config(_args):
    """显示当前配置（不显示 key 全文）。"""
    has_file = API_KEY_PATH.exists()
    print(f"Key 文件: {API_KEY_PATH}")
    print(f"  存在: {'✅' if has_file else '❌'}")
    if has_file:
        key = _load_key()
        print(f"  Key:  {key[:8]}...{key[-4:]}（共 {len(key)} 位）")
    print(f"API: {API_BASE}")
    print(f"默认模型: {DEFAULT_MODEL}")
    print(f"默认尺寸: {DEFAULT_SIZE}")
    print(f"配图 skill: {SKILL_DIR}")
    print(f"  存在: {'✅' if SKILL_DIR.exists() else '❌'}")
    print(f"输出目录: {DEFAULT_OUTPUT}")


def cmd_gen(args):
    """生成一张图。"""
    api_key = _load_key()
    DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else DEFAULT_OUTPUT / f"img_{int(subprocess.check_output(['date', '+%s']).decode().strip())}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "n": 1,
        "size": args.size,
    }

    if args.dry_run:
        print(f"DRY-RUN 模式")
        print(f"  URL: {API_BASE}/v1/images/generations")
        print(f"  Model: {args.model}")
        print(f"  Size: {args.size}")
        print(f"  Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
        print(f"  Out: {out_path}")
        print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
        return

    print(f"⏳ 调用 {args.model} 生成 {args.size} 图...", file=sys.stderr)
    # 用 curl 调（subprocess 跑更稳定）
    payload_str = json.dumps(payload, ensure_ascii=False)
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{API_BASE}/v1/images/generations",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", payload_str,
    ], capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"❌ curl 失败：{result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ 返回非 JSON：{result.stdout[:300]}", file=sys.stderr)
        sys.exit(1)

    if "data" not in data or not data["data"]:
        print(f"❌ 返回无 data：{json.dumps(data, ensure_ascii=False)[:300]}", file=sys.stderr)
        sys.exit(1)

    item = data["data"][0]
    if "b64_json" in item:
        b64 = item["b64_json"]
        img_bytes = base64.b64decode(b64)
        out_path.write_bytes(img_bytes)
        size_kb = len(img_bytes) // 1024
        print(f"✅ 已保存：{out_path} ({size_kb} KB)", file=sys.stderr)
    elif "url" in item:
        url = item["url"]
        if url.startswith("data:image/"):
            # 中转站格式：data:image/png;base64,xxx
            b64 = url.split(",", 1)[1]
            img_bytes = base64.b64decode(b64)
            out_path.write_bytes(img_bytes)
            size_kb = len(img_bytes) // 1024
            print(f"✅ 已保存（data URL 解码）：{out_path} ({size_kb} KB)", file=sys.stderr)
        else:
            # 公开 URL
            import urllib.request
            urllib.request.urlretrieve(url, out_path)
            print(f"✅ 已下载：{out_path}", file=sys.stderr)
    else:
        print(f"❌ 返回无 b64_json/url：{json.dumps(item, ensure_ascii=False)[:300]}", file=sys.stderr)
        sys.exit(1)

    # 输出关键信息
    print(json.dumps({
        "ok": True,
        "out": str(out_path),
        "size_kb": out_path.stat().st_size // 1024,
        "model": args.model,
        "size": args.size,
    }, ensure_ascii=False, indent=2))


def cmd_styles(_args):
    """列出归藏材质配图风格。"""
    print("📐 归藏材质配图风格（来自 /tmp/guizang-material-illustration/SKILL.md）\n")
    styles = [
        ("Cycle", "循环 / 反馈 / 迭代"),
        ("Pipeline", "有序步骤 / 路由 / 转换 / 工作流"),
        ("Hub-and-spoke", "一个中心协调多个分支"),
        ("Before/After", "状态变化 / 升级 / 迁移 / 对比"),
        ("Layer Stack", "架构 / 层级 / 依赖"),
        ("Data-first scene", "图表或数据嵌入主题场景"),
        ("Scientific mechanism", "物体 / 部件 / 力 / 反应 / 生物过程"),
        ("Text scene", "文学 / 历史 / 日常场景"),
    ]
    print(f"{'#':<3} {'结构':<25} {'适用'}")
    print("-" * 80)
    for i, (name, use) in enumerate(styles, 1):
        print(f"{i:<3} {name:<25} {use}")
    print("\n读 SKILL.md 第 5-7 步了解每种结构怎么用 prompt 描述")
    print("读 references/visual-style.md 看默认 3D Swiss editorial 风格 + 配色")
    print("读 references/prompt-patterns.md 看可复用 prompt 模板")


def cmd_template(args):
    """按配图 skill 的 prompt-patterns 模板生成。"""
    skill_ref = SKILL_DIR / "references" / "prompt-patterns.md"
    if not skill_ref.exists():
        print(f"❌ 找不到 {skill_ref}", file=sys.stderr)
        sys.exit(1)
    print(skill_ref.read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser(
        prog="image_gen",
        description="中转站生图 + 归藏材质配图 skill 本地化接口",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("config", help="显示当前配置").set_defaults(fn=cmd_config)
    sub.add_parser("styles", help="列出归藏材质配图风格").set_defaults(fn=cmd_styles)

    sp = sub.add_parser("gen", help="生成 1 张图")
    sp.add_argument("--prompt", required=True, help="中文/英文 prompt")
    sp.add_argument("--out", help="输出路径（默认 50_输出/公众号文章/imgs/img_xxx.png）")
    sp.add_argument("--size", default=DEFAULT_SIZE, help=f"尺寸（默认 {DEFAULT_SIZE}）")
    sp.add_argument("--model", default=DEFAULT_MODEL, help=f"模型（默认 {DEFAULT_MODEL}）")
    sp.add_argument("--dry-run", action="store_true", help="只显示请求不实际调用")
    sp.set_defaults(fn=cmd_gen)

    sp = sub.add_parser("template", help="读配图 skill 的 prompt-patterns 模板")
    sp.set_defaults(fn=cmd_template)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
