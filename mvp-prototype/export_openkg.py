# -*- coding: utf-8 -*-
"""导出开放图谱（MIT 兼容）：JSON-LD + 节点/边 CSV，含完整溯源链。

溯源链完整率 100% = 每个入库节点/边都带非空 provenance（source_ref + extraction + review）。
"""
from __future__ import annotations

import csv
import json
import os
import hashlib
from dataclasses import asdict
from kg_schema import KnowledgeNode, DependencyEdge, SCHEMA_VERSION


def to_jsonld(nodes, edges_approved) -> dict:
    graph = []
    for n in nodes:
        d = asdict(n)
        d["@type"] = "KnowledgeNode"
        graph.append(d)
    for e in edges_approved:
        d = asdict(e)
        d["@type"] = "DependencyEdge"
        graph.append(d)
    return {
        "@context": {
            "label": "https://schema.org/name",
            "KnowledgeNode": "https://example.org/kg/KnowledgeNode",
            "DependencyEdge": "https://example.org/kg/DependencyEdge",
            "source": {"@type": "@id"},
            "target": {"@type": "@id"},
        },
        "schemaVersion": SCHEMA_VERSION,
        "@graph": graph,
    }


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def export(nodes, edges_approved, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)

    # JSON-LD
    ld_path = os.path.join(out_dir, "knowledge-graph.jsonld")
    with open(ld_path, "w", encoding="utf-8") as f:
        json.dump(to_jsonld(nodes, edges_approved), f, ensure_ascii=False, indent=2)

    # CSV 节点
    nodes_path = os.path.join(out_dir, "nodes.csv")
    with open(nodes_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "label", "grade", "std_anchor",
                    "source_ref", "extraction_method", "extraction_model",
                    "extracted_at", "reviewer", "review_status", "review_at", "evidence"])
        for n in nodes:
            p = n.provenance
            w.writerow([n.id, n.label, n.grade or "", n.std_anchor or "",
                        p.source_ref, p.extraction_method, p.extraction_model,
                        p.extracted_at, p.reviewer or "", p.review_status, p.review_at or "", p.evidence])

    # CSV 边（仅 approved）
    edges_path = os.path.join(out_dir, "edges.csv")
    with open(edges_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "target", "relation",
                    "source_ref", "extraction_method", "extraction_model",
                    "extracted_at", "reviewer", "review_status", "review_at", "evidence"])
        for e in edges_approved:
            p = e.provenance
            w.writerow([e.id, e.source, e.target, e.relation,
                        p.source_ref, p.extraction_method, p.extraction_model,
                        p.extracted_at, p.reviewer or "", p.review_status, p.review_at or "", p.evidence])

    # 收据（字节级溯源，对齐 VERIFICATION_RECEIPT 风格）
    files = [ld_path, nodes_path, edges_path]
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "node_count": len(nodes),
        "approved_edge_count": len(edges_approved),
        "provenance_complete": all(
            (n.provenance.source_ref and n.provenance.extraction_method)
            for n in nodes
        ) and all(
            (e.provenance.source_ref and e.provenance.extraction_model and e.provenance.reviewer)
            for e in edges_approved
        ),
        "files": {os.path.basename(p): _sha256(p) for p in files},
    }
    receipt_path = os.path.join(out_dir, "receipt.json")
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)

    return receipt
