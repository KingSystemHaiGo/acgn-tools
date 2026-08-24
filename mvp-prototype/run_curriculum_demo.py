# -*- coding: utf-8 -*-
"""课标解析演示：结构化输入 -> seed 节点 + 已知前置边；溯源/锚定合规校验。"""
from __future__ import annotations

from curriculum_parser import parse
from review_gate import apply_review
from verification import verify

SAMPLE = """[领域] 数与代数
[学段] 小学
[主题] 小数的意义
[知识点] 小数与整数的位值关系
[知识点] 小数加减法（需先掌握：整数加减法、通分）
[主题] 分数的意义
[知识点] 分数表示整体的一部分
[知识点] 分数加减法（需先掌握：通分）"""


def main():
    nodes, edges = parse(SAMPLE)
    # 课标标注的前置边视为权威，经 consume-gate 标记 approved
    approved, _ = apply_review(edges, {e.id: "approve" for e in edges}, reviewer="curriculum")
    print(f"seed 节点: {len(nodes)}  已知前置边: {len(approved)}")
    r = verify(nodes, approved)
    print(f"通过:{r['passed']}  环:{r['has_cycle']}  "
          f"溯源率:{r['provenance_complete_rate']}  锚定率:{r['std_anchor_rate']}")
    for n in nodes:
        print(f"  {n.id} {n.label}  anchor={n.std_anchor}")


if __name__ == "__main__":
    main()
