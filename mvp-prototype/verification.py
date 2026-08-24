# -*- coding: utf-8 -*-
"""MVP 一致性校验：循环依赖检测 + 引用完整性 + 溯源/锚定合规。

支撑 RESEARCH-001 v1.0 MVP 验收口径里的"一致性校验 / 溯源链完整率 / 课标锚定率"。
全部离线可跑，不依赖外部 API。
"""
from __future__ import annotations
from typing import List, Dict, Any


def detect_cycles(edges) -> List[List[str]]:
    """检测依赖图中的有向环（DFS 三色标记）。返回环列表，每环是节点 id 序列。"""
    adj = {}
    for e in edges:
        adj.setdefault(e.source, []).append(e.target)
    nodes = set(adj.keys())
    for es in adj.values():
        nodes.update(es)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    cycles: List[List[str]] = []
    stack: List[str] = []

    def dfs(u):
        color[u] = GRAY
        stack.append(u)
        for v in adj.get(u, []):
            if color.get(v, WHITE) == GRAY:
                idx = stack.index(v)
                cycles.append(stack[idx:] + [v])
            elif color.get(v, WHITE) == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for n in list(color.keys()):
        if color[n] == WHITE:
            dfs(n)
    return cycles


def check_node_references(edges, nodes) -> List[str]:
    """依赖边端点必须都存在于节点集；返回悬空边 id 列表。"""
    ids = {n.id for n in nodes}
    dangling = []
    for e in edges:
        if e.source not in ids or e.target not in ids:
            dangling.append(e.id)
    return dangling


def check_provenance(nodes, edges) -> List[str]:
    """溯源链完整：节点/边 provenance 关键字段非空；返回不合规对象 id。"""
    bad = []
    for n in nodes:
        p = n.provenance
        if not (p.source_ref and p.extraction_method and p.extraction_model):
            bad.append(n.id)
    for e in edges:
        p = e.provenance
        if not (p.source_ref and p.extraction_method and p.extraction_model and p.reviewer):
            bad.append(e.id)
    return bad


def check_std_anchor(nodes) -> List[str]:
    """课标锚定：节点应有 std_anchor（锚定 2022 课标）；返回缺失节点 id。"""
    return [n.id for n in nodes if not n.std_anchor]


def verify(nodes, edges_approved) -> Dict[str, Any]:
    """汇总校验，返回报告。"""
    cycles = detect_cycles(edges_approved)
    dangling = check_node_references(edges_approved, nodes)
    provenance_bad = check_provenance(nodes, edges_approved)
    no_anchor = check_std_anchor(nodes)
    total_nodes = len(nodes)
    total_obj = total_nodes + len(edges_approved)
    report = {
        "node_count": total_nodes,
        "approved_edge_count": len(edges_approved),
        "cycles": cycles,
        "has_cycle": len(cycles) > 0,
        "dangling_edges": dangling,
        "provenance_incomplete": provenance_bad,
        "provenance_complete_rate": round(1 - len(provenance_bad) / max(1, total_obj), 4),
        "nodes_missing_std_anchor": no_anchor,
        "std_anchor_rate": round(1 - len(no_anchor) / max(1, total_nodes), 4),
        "passed": (not cycles) and (not dangling) and (not provenance_bad),
    }
    return report
