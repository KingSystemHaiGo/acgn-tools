# -*- coding: utf-8 -*-
"""consume-gate 人审协议。

依赖边必须人审后才写入已发布图谱（RESEARCH-001 子问题① + CatKing 对齐共识③）。
- apply_review(edges, decisions, reviewer): 应用人审决策。
- 只 approved 的边进入 published graph；rejected/edited/pending 不入库。
"""
from __future__ import annotations

import datetime as _dt
from typing import Tuple


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def apply_review(edges, decisions: dict, reviewer: str = "human-reviewer") -> Tuple[list, list]:
    """对候选边应用人审决策。

    decisions: {edge_id: "approve" | "reject" | "edit"}
    默认 approve（原型演示用；生产应逐条人工确认）。
    返回 (approved_edges, not_approved_edges)。
    """
    approved: list = []
    not_approved: list = []
    for e in edges:
        decision = decisions.get(e.id, "approve")
        e.provenance.review_status = "approved" if decision == "approve" else decision
        e.provenance.reviewer = reviewer
        e.provenance.review_at = _now()
        if decision == "approve":
            approved.append(e)
        else:
            not_approved.append(e)
    return approved, not_approved
