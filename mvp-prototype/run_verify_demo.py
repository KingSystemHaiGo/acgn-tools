# -*- coding: utf-8 -*-
"""一致性校验演示：正常图谱通过；注入循环依赖后被检出。

证明 verification.py 的循环依赖检测 / 引用完整性 / 溯源合规在校验环节真实生效。
"""
from __future__ import annotations

import datetime as _dt
from extractor import extract_heuristic
from review_gate import apply_review
from verification import verify
from kg_schema import DependencyEdge, Provenance

SAMPLE = (
    "数与代数领域包含整数、小数和分数。整数认识是后续学习的基础。"
    "小数的意义建立在整数位值制上。分数表示整体的一部分。"
    "分数的加减法需要先理解通分。小数与分数可以互相转化。"
)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def main():
    nodes, edges = extract_heuristic(SAMPLE, grade="小学")
    approved, _ = apply_review(edges, {e.id: "approve" for e in edges}, reviewer="demo-reviewer")

    print("== 正常图谱 ==")
    r1 = verify(nodes, approved)
    print(f"节点 {r1['node_count']}  边 {r1['approved_edge_count']}  "
          f"通过:{r1['passed']}  环:{r1['has_cycle']}  "
          f"溯源率:{r1['provenance_complete_rate']}  锚定率:{r1['std_anchor_rate']}")

    # 注入一个循环依赖：kp-006 -> kp-001（形成 1->2->...->6->1）
    cyc = DependencyEdge(
        id="edge-loop",
        source="kp-006",
        target="kp-001",
        relation="prerequisite",
        provenance=Provenance(
            source_ref="injected",
            extraction_method="heuristic-fallback",
            extraction_model="heuristic-v1",
            extracted_at=_now(),
            reviewer="demo-reviewer",
            review_status="approved",
            review_at=_now(),
        ),
    )
    approved2 = approved + [cyc]

    print("\n== 注入循环依赖后 ==")
    r2 = verify(nodes, approved2)
    print(f"通过:{r2['passed']}  环:{r2['has_cycle']}  检出环数:{len(r2['cycles'])}")
    for c in r2["cycles"]:
        print("  环: " + " -> ".join(c))


if __name__ == "__main__":
    main()
