# -*- coding: utf-8 -*-
"""MVP 教育知识图谱数据模型 + 溯源链（provenance）。

设计约束（来自 RESEARCH-001 v1.0 终稿）：
- 依赖边必须人审（consume-gate 语义）：review_status=pending 的边不写入已发布图谱。
- 每个节点/边带溯源 evidence 链：source_ref + extraction + review。
- 只存知识点 + 依赖边 + 课标锚点，不存教材原文（版权合规）。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

SCHEMA_VERSION = "mvp-kg-0.1"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


@dataclass
class Provenance:
    source_ref: str            # 课标条目 / 教材锚点（不存原文）
    extraction_method: str     # llm | heuristic-fallback
    extraction_model: str      # 模型名 或 heuristic-v1
    extracted_at: str
    reviewer: Optional[str] = None            # 人审者；pending 时为 None
    review_status: str = "pending"           # pending|approved|rejected|edited
    review_at: Optional[str] = None
    evidence: str = ""                        # 溯源引用（锚点描述，非原文复制）


@dataclass
class KnowledgeNode:
    id: str
    label: str
    grade: Optional[str] = None
    std_anchor: Optional[str] = None         # 课标锚点 id（19 锚点体系）
    provenance: Provenance = field(default_factory=lambda: Provenance("", "heuristic-fallback", "heuristic-v1", _now()))
    props: dict = field(default_factory=dict)


@dataclass
class DependencyEdge:
    id: str
    source: str               # 前置知识点 id
    target: str               # 后继知识点 id
    relation: str = "prerequisite"   # prerequisite | co_occurrence(不入库)
    provenance: Provenance = field(default_factory=lambda: Provenance("", "heuristic-fallback", "heuristic-v1", _now()))
    props: dict = field(default_factory=dict)


def node_hash(n: KnowledgeNode) -> str:
    blob = json.dumps(asdict(n), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def edge_hash(e: DependencyEdge) -> str:
    blob = json.dumps(asdict(e), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
