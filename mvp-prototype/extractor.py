# -*- coding: utf-8 -*-
"""候选微知识点 + 依赖边抽取。

- extract_with_llm(text, model): 真实 LLM 调用占位（需模型 API）。
- extract_heuristic(text): 离线 fallback，无需 API，供原型端到端演示跑通。

MVP 生产路径用 LLM（抽取质量高）；原型演示用 heuristic（可离线验证架构）。
"""
from __future__ import annotations

import re
import datetime as _dt
from typing import Tuple
from kg_schema import KnowledgeNode, DependencyEdge, Provenance


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def extract_with_llm(text: str, model: str = "hy3-free") -> Tuple[list, list]:
    """真实 LLM 抽取占位。

    生产实现：调用模型 API，传入课标/教材文本，prompt 要求返回
    {"nodes":[{"id","label","grade","std_anchor"}], "edges":[{"source","target","relation"}]}。
    返回前包装 Provenance(extraction_method="llm", extraction_model=model)。
    原型不接入外部 API，故抛 NotImplementedError。
    """
    raise NotImplementedError("LLM 抽取需接入模型 API；原型演示请用 extract_heuristic。")


def extract_heuristic(text: str, grade: str = "小学") -> Tuple[list, list]:
    """极简离线抽取：按句切分 -> 每句一个候选知识点；按出现顺序生成前序依赖候选。"""
    nodes: list = []
    sentences = [s.strip() for s in re.split(r"[。；;]", text) if len(s.strip()) >= 4]
    edges: list = []
    prev_id = None
    for i, s in enumerate(sentences):
        nid = f"kp-{i + 1:03d}"
        node = KnowledgeNode(
            id=nid,
            label=s[:24],
            grade=grade,
            provenance=Provenance(
                source_ref="sample-curriculum",
                extraction_method="heuristic-fallback",
                extraction_model="heuristic-v1",
                extracted_at=_now(),
                evidence=s[:60],
            ),
        )
        nodes.append(node)
        if prev_id is not None:
            eid = f"edge-{prev_id}->{nid}"
            edges.append(DependencyEdge(
                id=eid,
                source=prev_id,
                target=nid,
                relation="prerequisite",
                provenance=Provenance(
                    source_ref="sample-curriculum",
                    extraction_method="heuristic-fallback",
                    extraction_model="heuristic-v1",
                    extracted_at=_now(),
                    evidence=f"顺序共现：{prev_id} 先于 {nid} 出现",
                ),
            ))
        prev_id = nid
    return nodes, edges
