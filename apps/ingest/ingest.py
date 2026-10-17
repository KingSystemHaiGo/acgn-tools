#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest.py — 一句话入口 CLI（M2 切片 1）
=====================================
用法：
  python3 apps/ingest/ingest.py "项目 A 的截止日期是 9 月 19 日" "项目 A 的截止日期改成 10 月 3 日"
  echo "负责人是张三" | python3 apps/ingest/ingest.py --stdin --server http://127.0.0.1:8000
  python3 apps/ingest/ingest.py --dry-run "价格是 30 元"

做三件事：
1. 归一化：一句话 → (subject, predicate)，同一主题同一谓词的多句归入同一 claim（claim_norm.py）
2. 入库：对每个 claim 调 knowledge-map `POST /api/import`（同批多行 = 同 claim 多断言）
3. 报冲突：`GET /api/conflicts` 取回该 claim 的裁决结果，直接用人话打出来

纪律：
- 网络失败必须显式非零退出（不许静默吞掉，否则「已入库」是假绿）
- `--dry-run` 完全离线：只打印归并计划，用于评审和 fixture 生成
- 输出里同时给 raw 与 norm 两份值，判冲突看 norm、人读看 raw
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

from claim_norm import Claim, group


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_sentences(args: argparse.Namespace) -> list[str]:
    sentences = list(args.sentences)
    if args.stdin:
        sentences += [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    return [s for s in sentences if s.strip()]


def print_plan(groups: dict[str, list[Claim]]) -> None:
    for anchor, claims in groups.items():
        if not anchor:
            for c in claims:
                print(f"  [UNPARSED] {c.reason} → 原文未入库（需人工补谓词或改写）")
            continue
        print(f"  claim {anchor}")
        for c in claims:
            flag = "" if c.value_raw == c.value_norm else f"  (norm: {c.value_norm})"
            print(f"    - {c.value_raw}{flag}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="一句话入口：说一句话 → 入库 → 报冲突")
    ap.add_argument("sentences", nargs="*", help="一句话（可多句，同主题同谓词自动归并）")
    ap.add_argument("--server", default="http://127.0.0.1:8000", help="knowledge-map 服务地址")
    ap.add_argument("--stdin", action="store_true", help="从 stdin 每行读一句话")
    ap.add_argument("--dry-run", action="store_true", help="只打印归并计划，不联网")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args(argv)

    sentences = collect_sentences(args)
    if not sentences:
        print("没有输入（给句子，或用 --stdin）", file=sys.stderr)
        return 2

    groups = group(sentences)
    ok_groups = {a: cs for a, cs in groups.items() if a}

    if args.dry_run:
        if args.json:
            print(json.dumps(
                {a: [{"value_raw": c.value_raw, "value_norm": c.value_norm} for c in cs] for a, cs in groups.items()},
                ensure_ascii=False, indent=2))
        else:
            print(f"归并计划（{len(sentences)} 句 → {len(ok_groups)} 个 claim）：")
            print_plan(groups)
        return 0

    if not ok_groups:
        print("没有可入库的句子（全部 UNPARSED）", file=sys.stderr)
        print_plan(groups)
        return 3

    imported: list[dict[str, Any]] = []
    errors: list[str] = []
    for anchor, claims in ok_groups.items():
        body = {"title": anchor, "text": "\n".join(c.as_line() for c in claims)}
        try:
            imported.append(_post(f"{args.server}/api/import", body))
        except urllib.error.URLError as exc:
            errors.append(f"{anchor}: {exc}")

    if errors:
        for e in errors:
            print(f"ERROR 入库失败 {e}", file=sys.stderr)
        return 4  # 显式失败：不许当成功

    claim_ids = [r.get("claim_id") for r in imported]
    conflicts: list[dict[str, Any]] = []
    try:
        payload = _get(f"{args.server}/api/conflicts")
        all_conflicts = payload.get("conflicts", payload if isinstance(payload, list) else [])
        conflicts = [c for c in all_conflicts if c.get("claim_id") in claim_ids]
    except urllib.error.URLError as exc:
        print(f"WARN 冲突查询失败（入库已成功）：{exc}", file=sys.stderr)

    if args.json:
        print(json.dumps({"imported": imported, "conflicts": conflicts}, ensure_ascii=False, indent=2))
        return 0

    total_entries = sum(r.get("imported", 0) for r in imported)
    print(f"已入库 {total_entries} 条，{len(imported)} 个 claim：")
    for r in imported:
        print(f"  {r.get('claim_id')}  ({r.get('imported')} 条)")
    if not conflicts:
        print("无冲突。")
        return 0

    print(f"发现 {len(conflicts)} 处冲突：")
    for c in conflicts:
        ev = c.get("evidence") or []
        print(f"  [{c.get('claim_id')}] {c.get('verdict', c.get('status', 'CONFLICTED'))}")
        for triple in ev:
            if isinstance(triple, (list, tuple)) and len(triple) >= 3:
                print(f"    字段 {triple[0]}｜修订 {triple[1]}｜{triple[2]}")
            else:
                print(f"    {triple}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
