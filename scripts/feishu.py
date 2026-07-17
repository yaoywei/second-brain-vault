#!/usr/bin/env python3
"""
feishu.py — 飞书内容中台本地化接口

封装 lark-cli base 调用，提供：
- feishu.py tables            列出 16 张表
- feishu.py schema 13          列出某张表的字段（从 _feishu_raw/_schema_cache.json 读）
- feishu.py list 13            列出表内所有记录（带过滤）
- feishu.py find 13 <keyword>  按关键词搜索
- feishu.py show <record_id>   按 record_id 查单条
- feishu.py stats 13           统计分布（按栏目/标签/优先级）
- feishu.py add 13 --data '{...}'    新增
- feishu.py update 13 <record_id> --field value    更新
- feishu.py upsert 13 <record_id> --data '{...}'   创建或更新
- feishu.py sync 13            拉一遍刷新本地 schema 缓存（不拉数据，避免冗余）

设计原则（师傅 7/16 要求）：
- 数据本身不落地（除非调用方主动 add）
- schema 和接口本地化
- 一句话能查到任何东西
"""

from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# === 配置 ===
BASE_TOKEN = "TejybyBY0a4Q5bsOYmucwzVTnwf"
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
RAW_DIR = VAULT_ROOT / "40_资源" / "工具收藏" / "_feishu_raw"
SCHEMA_CACHE = RAW_DIR / "_schema_cache.json"

# 16 表 table_id 速查表（来源：Hermes v4 SKILL.md + lark-mcp 实测）
TABLES = {
    "00": ("Hermes取料规则", "tblGmclVtJWsrzUQ"),
    "01": ("外部资料库", "tblKhjvH1gd12OHh"),
    "02": ("流程拆解库", "tbliBzDSxrXqNcFt"),
    "03": ("问题与痛点库", "tbluJ4dzXodscL8a"),
    "04": ("观点反常识原子库", "tblos5Xt14CM8phY"),
    "05": ("改造方案库", "tblk14J0YUVYWfEg"),
    "06": ("实战案例库", "tblMfktmt48QO3Ik"),
    "07": ("选题生产表", "tblXdtaMSR96uhbb"),
    "08": ("精选生产池", "tbljsqpHs7l9N0Er"),
    "09": ("发布队列", "tblXhlOuHFuBAGTF"),
    "10": ("扩展采集入口", "tbl5CfYGmX72pHc3"),
    "11": ("源资料精洗索引", "tblJC15jTqSpYaPb"),
    "12": ("云盘删除验收表", "tblGlyT6d4eyubR6"),
    "13": ("可独立取料原子库", "tbl1bxlcfUJd5rXR"),
    "14": ("题材组合模板", "tblYthCfyozMquPW"),
    "15": ("视觉素材库", "tbldAE1lDtns5SVs"),
    "16": ("跨平台适配表", "tblzd6LInkRTC2oh"),
}

# 表别名（友好名）
TABLE_ALIAS = {
    "rule": "00", "rules": "00",
    "material": "01", "materials": "01", "ext": "01",
    "flow": "02", "flows": "02", "process": "02",
    "pain": "03", "pains": "03", "faq": "03",
    "view": "04", "views": "04", "opinion": "04",
    "refactor": "05", "refactorings": "05",
    "case": "06", "cases": "06",
    "topic-pool": "08", "pool": "08", "topics": "08",
    "publish": "09", "queue": "09",
    "atom": "13", "atoms": "13",
    "template": "14", "templates": "14",
    "visual": "15", "visuals": "15", "image": "15",
    "xplatform": "16", "multi": "16",
    "对标账号": "tblzBE96JXGz6iUE",  # 2026-07-16 新建：次幂数据找对标专用
    "benchmarks": "tblzBE96JXGz6iUE",
}


def resolve_table(name_or_id: str) -> tuple[str, str, str]:
    """返回 (编号, 中文名, table_id)。支持：13 / atom / atoms / 对标账号 / tblxxx"""
    s = name_or_id.strip()
    if s in TABLE_ALIAS:
        s = TABLE_ALIAS[s]
    s_lower = s.lower()
    if s_lower in TABLES:
        cn, tid = TABLES[s_lower]
        return s_lower, cn, tid
    # 可能是 table_id（以 tbl 开头）
    if s.startswith("tbl"):
        # 反查 Chinese name / 编号
        for k, (cn, tid) in TABLES.items():
            if tid == s:
                return k, cn, tid
        # 不在 TABLES 字典里也接受（如新建的 tblzBE96JXGz6iUE）
        return ("17", "对标账号", s)
    # 也按 case-insensitive 检查
    for k, (cn, tid) in TABLES.items():
        if tid == s:
            return k, cn, tid
    raise ValueError(f"未知表：{name_or_id}（可用：00-16 或 {', '.join(TABLE_ALIAS.keys())}）")


# === lark-cli 调用 ===
def lark(cmd: list[str], timeout: int = 60) -> dict:
    """调一次 lark-cli，返回 JSON。"""
    full = ["lark-cli"] + cmd
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": {"type": "timeout", "message": f"timeout after {timeout}s"}}
    if r.returncode != 0:
        return {"ok": False, "error": {"type": "exit", "message": r.stderr or r.stdout}}
    out = r.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": {"type": "json", "message": out[:500]}}


# === 子命令 ===
def cmd_tables(_args):
    """列出 16 张表"""
    print(f"{'#':<3} {'编号':<4} {'中文名':<22} {'table_id'}")
    print("-" * 70)
    for k in sorted(TABLES.keys()):
        cn, tid = TABLES[k]
        print(f"{k:<3} {k:<4} {cn:<22} {tid}")
    print(f"\n别名：{', '.join(sorted(TABLE_ALIAS.keys()))}")
    print(f"Base token：{BASE_TOKEN}")


def cmd_schema(args):
    """列出某张表的字段。优先读本地缓存，没有就调 lark-cli 拉一份。"""
    _, cn, tid = resolve_table(args.table)
    cache_key = f"{args.table}"
    cache = {}
    if SCHEMA_CACHE.exists():
        cache = json.loads(SCHEMA_CACHE.read_text())

    if cache_key in cache:
        fields = cache[cache_key]
        print(f"# {args.table}｜{cn} 字段（来自本地缓存 {SCHEMA_CACHE.name}）\n")
    else:
        print(f"# {args.table}｜{cn} 字段（远程拉取，请稍候…）\n", file=sys.stderr)
        r = lark(["base", "+field-list", "--base-token", BASE_TOKEN,
                  "--table-id", tid, "--format", "json"])
        if not r.get("ok"):
            print(f"❌ 拉取失败：{r.get('error')}", file=sys.stderr)
            sys.exit(1)
        # 实际路径：data.fields 是数组，每个元素含 name/type/options
        items = (r.get("data") or {}).get("fields") or []
        fields = [{"id": f.get("id"), "name": f.get("name"),
                   "type": f.get("type"), "options": f.get("options")}
                  for f in items if isinstance(f, dict)]
        # 缓存
        cache[cache_key] = fields
        SCHEMA_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2))

    print(f"{'#':<3} {'字段名':<24} {'类型':<10} {'枚举值/备注'}")
    print("-" * 90)
    for i, f in enumerate(fields, 1):
        opts = f.get("options") or []
        if isinstance(opts, list) and opts and isinstance(opts[0], dict):
            opt_str = " / ".join(o.get("name", "?") for o in opts[:8])
            if len(opts) > 8:
                opt_str += f" …(+{len(opts)-8})"
        else:
            opt_str = ""
        print(f"{i:<3} {f.get('name',''):<24} {str(f.get('type','')):<10} {opt_str}")


def _fetch_field_id_to_name(tid: str) -> dict[str, str]:
    """返回 {field_id: field_name}。从 schema 缓存读。"""
    cache = json.loads(SCHEMA_CACHE.read_text()) if SCHEMA_CACHE.exists() else {}
    for k, v in cache.items():
        if TABLES[k][1] == tid:
            return {f["id"]: f["name"] for f in v if isinstance(f, dict) and f.get("id") and f.get("name")}
    r = lark(["base", "+field-list", "--base-token", BASE_TOKEN,
              "--table-id", tid, "--format", "json"], timeout=30)
    items = (r.get("data") or {}).get("fields") or []
    return {f["id"]: f["name"] for f in items if isinstance(f, dict) and f.get("id") and f.get("name")}


def _normalize_records(raw_data: dict | list, field_id_to_name: dict | None = None,
                       record_ids: list[str] | None = None) -> list[dict]:
    """lark-cli 返回 data = {data: [...], field_id_list: [...], record_id_list: [...]}
    每条 record 是 list（值数组），位置严格对应 field_id_list。"""
    if isinstance(raw_data, dict):
        rows = raw_data.get("data") or []
        ids = raw_data.get("record_id_list") or record_ids or []
        field_ids = raw_data.get("field_id_list") or []
    else:
        rows = raw_data
        ids = record_ids or []
        field_ids = []
    mapping = field_id_to_name or {}
    out = []
    for i, row in enumerate(rows):
        if isinstance(row, dict):
            out.append({"record_id": ids[i] if i < len(ids) else "?", **row})
            continue
        if isinstance(row, list):
            rec = {"record_id": ids[i] if i < len(ids) else "?"}
            for j, val in enumerate(row):
                if j < len(field_ids):
                    fname = mapping.get(field_ids[j], field_ids[j])
                else:
                    fname = f"_f{j}"
                rec[fname] = val
            out.append(rec)
    return out


def _fetch_field_names(tid: str) -> list[str]:
    """从 schema 缓存返回 field_name 列表（顺序与 lark 返回一致）。"""
    cache = json.loads(SCHEMA_CACHE.read_text()) if SCHEMA_CACHE.exists() else {}
    for k, v in cache.items():
        if TABLES[k][1] == tid:
            return [f["name"] for f in v if isinstance(f, dict) and f.get("name")]
    r = lark(["base", "+field-list", "--base-token", BASE_TOKEN,
              "--table-id", tid, "--format", "json"], timeout=30)
    items = (r.get("data") or {}).get("fields") or []
    return [f["name"] for f in items if isinstance(f, dict) and f.get("name")]


def cmd_list(args):
    """列记录（带过滤）。"""
    _, cn, tid = resolve_table(args.table)
    filter_json = None
    if args.filter:
        try:
            filter_json = json.loads(args.filter)
        except json.JSONDecodeError:
            field, op, value = [s.strip() for s in args.filter.split(",", 2)]
            operator = {"==": "is", "contains": "contains", "intersects": "intersects"}.get(op, "contains")
            filter_json = {"logic": "and",
                           "conditions": [[field, operator, value]]}
    sort_json = json.dumps([{"field": args.sort, "desc": args.desc}]) if args.sort else None
    cmd = ["base", "+record-list",
           "--base-token", BASE_TOKEN, "--table-id", tid,
           "--limit", str(args.limit), "--format", "json"]
    if filter_json:
        cmd.extend(["--filter-json", json.dumps(filter_json)])
    if sort_json:
        cmd.extend(["--sort-json", sort_json])

    print(f"⏳ 拉取 {args.table}｜{cn}（limit={args.limit}）…", file=sys.stderr)
    r = lark(cmd, timeout=120)
    if not r.get("ok"):
        print(f"❌ {r.get('error')}", file=sys.stderr)
        sys.exit(1)

    field_id_map = _fetch_field_id_to_name(tid)
    records = _normalize_records(r.get("data") or {}, field_id_map)
    print(f"✅ 拉到 {len(records)} 条\n")
    _print_records(records, max_rows=args.limit)


def cmd_find(args):
    """按关键词搜索（用 +record-search）。"""
    _, cn, tid = resolve_table(args.table)
    # 默认用主字段
    DEFAULT_SEARCH_FIELDS = {
        "08": ["选题标题"],
        "13": ["原子标题", "原子内容"],
        "06": ["案例名称"],
    }
    fields = args.fields or DEFAULT_SEARCH_FIELDS.get(args.table, ["标题"])
    cmd = ["base", "+record-search",
           "--base-token", BASE_TOKEN, "--table-id", tid,
           "--keyword", args.keyword, "--limit", str(args.limit),
           "--format", "json"]
    for f in fields:
        cmd.extend(["--search-field", f])
    print(f"⏳ 搜索 {args.table}｜{cn} 关键词「{args.keyword}」…", file=sys.stderr)
    r = lark(cmd, timeout=120)
    if not r.get("ok"):
        print(f"❌ {r.get('error')}", file=sys.stderr)
        sys.exit(1)
    field_id_map = _fetch_field_id_to_name(tid)
    records = _normalize_records(r.get("data") or {}, field_id_map)
    print(f"✅ 命中 {len(records)} 条\n")
    _print_records(records, max_rows=args.limit)


def cmd_show(args):
    """按 record_id 查单条。"""
    _, cn, tid = resolve_table(args.table)
    cmd = ["base", "+record-get",
           "--base-token", BASE_TOKEN,
           "--table-id", tid,
           "--record-id", args.record_id,
           "--format", "json"]
    r = lark(cmd, timeout=30)
    if not r.get("ok"):
        print(f"❌ {r.get('error')}", file=sys.stderr)
        sys.exit(1)
    raw = (r.get("data") or {}).get("data") or (r.get("data") or {}).get("record") or r.get("data")
    if isinstance(raw, list) and raw:
        raw = raw[0]
    field_names = _fetch_field_names(tid)
    records = _normalize_records([raw] if raw else [], field_names)
    if records:
        print(json.dumps(records[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(raw, ensure_ascii=False, indent=2))


def cmd_stats(args):
    """统计某表的字段分布。"""
    _, cn, tid = resolve_table(args.table)
    print(f"⏳ 统计 {args.table}｜{cn}…", file=sys.stderr)
    r = lark(["base", "+record-list",
              "--base-token", BASE_TOKEN, "--table-id", tid,
              "--limit", "200", "--format", "json"], timeout=120)
    if not r.get("ok"):
        print(f"❌ {r.get('error')}", file=sys.stderr)
        sys.exit(1)
    field_id_map = _fetch_field_id_to_name(tid)
    field_names = list(field_id_map.values())
    records = _normalize_records(r.get("data") or {}, field_id_map)
    if not records:
        print("（空表）")
        return
    print(f"📊 {args.table}｜{cn} · 共 {len(records)} 条\n")
    # 自动识别枚举/多选字段：只统计 schema 类型是 select 的字段
    cache = json.loads(SCHEMA_CACHE.read_text()) if SCHEMA_CACHE.exists() else {}
    select_fields = []
    for k, v in cache.items():
        if TABLES[k][1] == tid:
            for f in v:
                if isinstance(f, dict):
                    # select 字段一定有 options 列表（即使为空），text/number 没有
                    if f.get("options") is not None or f.get("type") in ("select", "multi-select"):
                        select_fields.append(f.get("name"))
    KEY_FIELDS = select_fields or ["栏目", "栏目分布", "类型", "状态", "优先级", "证据等级",
                                    "Hermes使用状态", "原子类型", "文章类型", "目标读者",
                                    "适用栏目", "适用标签", "生产状态"]
    for kf in KEY_FIELDS:
        if kf not in field_names:
            continue
        counter: dict[str, int] = {}
        for rec in records:
            v = rec.get(kf)
            if v is None or v == "":
                continue
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, dict):
                        x = x.get("name") or x.get("text") or json.dumps(x)
                    s = str(x)
                    if len(s) > 40:  # 跳过 text 误匹（使用边界内容很长）
                        continue
                    counter[s] = counter.get(s, 0) + 1
            elif isinstance(v, dict):
                v = v.get("name") or v.get("text") or json.dumps(v)
                counter[str(v)] = counter.get(str(v), 0) + 1
            else:
                s = str(v)
                if len(s) > 40:
                    continue
                counter[s] = counter.get(s, 0) + 1
        if counter:
            print(f"## {kf}")
            for k, v in sorted(counter.items(), key=lambda x: -x[1])[:10]:
                bar = "█" * min(40, v)
                print(f"  {v:>4} {bar} {k}")
            if len(counter) > 10:
                print(f"  … 还有 {len(counter)-10} 项")
            print()


def cmd_add(args):
    """新增一条。"""
    _, cn, tid = resolve_table(args.table)
    data = json.loads(args.data)
    cmd = ["base", "+record-upsert",
           "--base-token", BASE_TOKEN, "--table-id", tid,
           "--json", json.dumps(data, ensure_ascii=False),
           "--format", "json"]
    if args.dry_run:
        cmd.append("--dry-run")
    r = lark(cmd, timeout=30)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_update(args):
    """更新一条。"""
    _, cn, tid = resolve_table(args.table)
    cmd = ["base", "+record-upsert",
           "--base-token", BASE_TOKEN, "--table-id", tid,
           "--record-id", args.record_id,
           "--json", json.dumps({args.field: args.value}, ensure_ascii=False),
           "--format", "json"]
    if args.dry_run:
        cmd.append("--dry-run")
    r = lark(cmd, timeout=30)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_sync(args):
    """刷新 schema 缓存（不拉数据，避免 vault 冗余）。"""
    cache = {}
    if SCHEMA_CACHE.exists() and not args.force:
        cache = json.loads(SCHEMA_CACHE.read_text())
    tables_to_sync = [args.table] if args.table else sorted(TABLES.keys())
    for k in tables_to_sync:
        cn, tid = TABLES[k]
        print(f"  ⏳ {k}｜{cn}…", file=sys.stderr)
        r = lark(["base", "+field-list", "--base-token", BASE_TOKEN,
                  "--table-id", tid, "--format", "json"])
        if not r.get("ok"):
            print(f"  ❌ {k} 失败：{r.get('error')}", file=sys.stderr)
            continue
        items = (r.get("data") or {}).get("fields") or []
        cache[k] = [{"id": f.get("id"), "name": f.get("name"),
                     "type": f.get("type"), "options": f.get("options")}
                    for f in items if isinstance(f, dict)]
    SCHEMA_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    print(f"✅ schema 缓存已更新 → {SCHEMA_CACHE.relative_to(VAULT_ROOT)}")


# === 工具 ===
def _print_records(records: list[dict], max_rows: int):
    if not records:
        print("（无记录）")
        return
    # 提取主字段（一般是第一个 text 字段）
    for i, rec in enumerate(records[:max_rows], 1):
        if not isinstance(rec, dict):
            continue
        rid = rec.get("record_id") or rec.get("id") or "?"
        title_field = None
        for k in ["原子标题", "选题标题", "案例名称", "标题", "Name", "name", "title", "Topic"]:
            if k in rec:
                title_field = rec[k]
                break
        if not title_field:
            title_field = rec.get("fields", [{}])[0] if rec.get("fields") else {}
        title = title_field if isinstance(title_field, str) else (
            title_field.get("text") or title_field.get("name") or json.dumps(title_field)[:60]
            if isinstance(title_field, dict) else str(title_field)[:60])
        # 主字段是数组（如 enum select）→ 取第一个
        if isinstance(title, list):
            if title and isinstance(title[0], dict):
                title = title[0].get("name") or title[0].get("text") or json.dumps(title[0])[:60]
            else:
                title = str(title[0]) if title else ""
        print(f"  [{i:>3}] {rid:<18}  {str(title)[:60]}")
    if len(records) > max_rows:
        print(f"\n（还有 {len(records)-max_rows} 条未显示，加 --limit 调大）")


# === main ===
def main():
    p = argparse.ArgumentParser(
        prog="feishu",
        description="飞书内容中台本地化接口（封装 lark-cli）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tables", help="列出 16 张表").set_defaults(fn=cmd_tables)

    sp = sub.add_parser("schema", help="列某张表的字段（优先本地缓存）")
    sp.add_argument("table", help="表编号（00-16）或别名（atom/topics）")
    sp.set_defaults(fn=cmd_schema)

    sp = sub.add_parser("list", help="列记录")
    sp.add_argument("table")
    sp.add_argument("--filter", help='过滤 JSON 或 "field,op,value"')
    sp.add_argument("--sort", help="排序字段名")
    sp.add_argument("--desc", action="store_true")
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(fn=cmd_list)

    sp = sub.add_parser("find", help="按关键词搜索")
    sp.add_argument("table")
    sp.add_argument("keyword")
    sp.add_argument("--fields", nargs="+", help="搜索字段名（默认全文）")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(fn=cmd_find)

    sp = sub.add_parser("show", help="查单条")
    sp.add_argument("table")
    sp.add_argument("record_id")
    sp.set_defaults(fn=cmd_show)

    sp = sub.add_parser("stats", help="统计字段分布")
    sp.add_argument("table")
    sp.set_defaults(fn=cmd_stats)

    sp = sub.add_parser("add", help="新增")
    sp.add_argument("table")
    sp.add_argument("--data", required=True, help="字段 JSON")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(fn=cmd_add)

    sp = sub.add_parser("update", help="更新一字段")
    sp.add_argument("table")
    sp.add_argument("record_id")
    sp.add_argument("--field", required=True)
    sp.add_argument("--value", required=True)
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(fn=cmd_update)

    sp = sub.add_parser("sync", help="刷新 schema 缓存（不拉数据）")
    sp.add_argument("table", nargs="?", help="不指定则同步全部 16 表")
    sp.add_argument("--force", action="store_true", help="覆盖已有缓存")
    sp.set_defaults(fn=cmd_sync)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
