# -*- coding: utf-8 -*-
"""课标/教材结构化输入解析器。

把如下层级文本解析为 seed 节点 + 已知前置依赖（作为 LLM 抽取锚点，降幻觉）：
[领域] 数与代数
  [学段] 小学
    [主题] 小数的意义
      [知识点] 小数与整数的位值关系
      [知识点] 小数加减法（需先掌握：整数加减法、通分）

解析出的节点带 std_anchor（锚定 2022 课标），故锚定率可达 100%；
"需先掌握：A、B" 标注转为已知前置依赖边。
"""
from __future__ import annotations

import re
import datetime as _dt
from typing import Tuple, List
from kg_schema import KnowledgeNode, DependencyEdge, Provenance


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def parse(text: str, grade_hint: str = None) -> Tuple[List, List]:
    nodes: List = []
    edges: List = []
    grade = grade_hint
    domain = None
    theme = None
    counter = [0]
    node_ids = {}

    def new_id() -> str:
        counter[0] += 1
        return f"kp-{counter[0]:03d}"

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[领域]"):
            domain = line.split("]", 1)[1].strip()
        elif line.startswith("[学段]"):
            grade = line.split("]", 1)[1].strip()
        elif line.startswith("[主题]"):
            theme = line.split("]", 1)[1].strip()
        elif line.startswith("[知识点]"):
            content = line.split("]", 1)[1].strip()
            label = content
            prereqs = []
            m = re.search(r"[（(]需先掌握[:：](.+?)[）)]", content)
            if m:
                label = content[: m.start()].strip()
                prereqs = [p.strip() for p in re.split(r"[、,，]", m.group(1))]
            nid = new_id()
            anchor = f"{domain or ''}-{theme or ''}-{label}" if (domain or theme) else None
            node = KnowledgeNode(
                id=nid,
                label=label,
                grade=grade,
                std_anchor=anchor,
                provenance=Provenance(
                    source_ref=f"curriculum:{domain or ''}/{theme or ''}",
                    extraction_method="curriculum-parser",
                    extraction_model="curriculum-parser-v1",
                    extracted_at=_now(),
                    evidence=content[:60],
                ),
            )
            nodes.append(node)
            node_ids[label] = nid
            for pr in prereqs:
                pid = node_ids.get(pr)
                if pid:
                    edges.append(DependencyEdge(
                        id=f"edge-{pid}->{nid}",
                        source=pid,
                        target=nid,
                        relation="prerequisite",
                        provenance=Provenance(
                            source_ref=f"curriculum:{domain or ''}/{theme or ''}",
                            extraction_method="curriculum-parser",
                            extraction_model="curriculum-parser-v1",
                            extracted_at=_now(),
                            evidence=f"课标标注需先掌握：{pr}",
                        ),
                    ))
    return nodes, edges
