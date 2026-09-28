# -*- coding: utf-8 -*-
"""端到端演示：样例课标文本 -> 抽取 -> 人审(全 approve) -> 导出开放图谱 + 收据。

无需任何外部 API，离线跑通，验证 MVP 架构（抽取 -> consume-gate -> 溯源导出）。
"""
from __future__ import annotations

import json
import os
from extractor import extract_heuristic
from review_gate import apply_review
from export_openkg import export

SAMPLE = (
    "数与代数领域包含整数、小数和分数。整数认识是后续学习的基础。"
    "小数的意义建立在整数位值制上。分数表示整体的一部分。"
    "分数的加减法需要先理解通分。小数与分数可以互相转化。"
)


def main():
    nodes, edges = extract_heuristic(SAMPLE, grade="小学")
    decisions = {e.id: "approve" for e in edges}
    approved, _ = apply_review(edges, decisions, reviewer="demo-reviewer")
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    receipt = export(nodes, approved, out_dir)
    print(f"节点数: {len(nodes)}   候选边: {len(edges)}   人审通过(入库): {len(approved)}")
    print(f"溯源链完整: {receipt['provenance_complete']}")
    print(f"输出目录: {out_dir}")
    print("收据:")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
