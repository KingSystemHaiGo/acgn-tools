# -*- coding: utf-8 -*-
"""consume-gate 人审 CLI：把候选依赖边经人审后入库并校验。

用法：
  python3 review_cli.py --auto-approve            # 演示：批量 approve
  python3 review_cli.py --decisions d.json        # 按 d.json {edge_id: approve|reject|edit}
  python3 review_cli.py --interactive             # 逐条交互确认（a/r/e）
"""
from __future__ import annotations

import argparse
import json
import os
from extractor import extract_heuristic
from review_gate import apply_review
from verification import verify
from export_openkg import export

SAMPLE = (
    "数与代数领域包含整数、小数和分数。整数认识是后续学习的基础。"
    "小数的意义建立在整数位值制上。分数表示整体的一部分。"
    "分数的加减法需要先理解通分。小数与分数可以互相转化。"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interactive", action="store_true", help="逐条交互确认")
    ap.add_argument("--decisions", help="decisions.json: {edge_id: approve|reject|edit}")
    ap.add_argument("--auto-approve", action="store_true", help="批量 approve（演示默认）")
    ap.add_argument("--reviewer", default="reviewer")
    args = ap.parse_args()

    nodes, edges = extract_heuristic(SAMPLE, grade="小学")

    if args.interactive:
        decisions = {}
        for e in edges:
            ans = input(f"{e.id} ({e.source}->{e.target}) [a/r/e]? ").strip().lower()
            decisions[e.id] = {"a": "approve", "r": "reject", "e": "edit"}.get(ans, "approve")
    elif args.decisions:
        decisions = json.load(open(args.decisions, encoding="utf-8"))
    else:
        decisions = {e.id: "approve" for e in edges}

    approved, not_appr = apply_review(edges, decisions, reviewer=args.reviewer)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    export(nodes, approved, out)
    r = verify(nodes, approved)
    print(f"候选边 {len(edges)}  入库 {len(approved)}  不入库 {len(not_appr)}")
    print(f"校验通过:{r['passed']}  环:{r['has_cycle']}  "
          f"溯源率:{r['provenance_complete_rate']}  锚定率:{r['std_anchor_rate']}")


if __name__ == "__main__":
    main()
