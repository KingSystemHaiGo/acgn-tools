# -*- coding: utf-8 -*-
"""候选微知识点 + 依赖边抽取。

- extract_with_llm(text, model, base_url, api_key): 真实 LLM 抽取（OpenAI 兼容 chat/completions）。
- extract_heuristic(text): 离线 fallback，无需 API，供原型端到端演示跑通。

MVP 生产路径用 LLM；原型演示用 heuristic（可离线验证架构）。
"""
from __future__ import annotations

import os
import re
import json
import datetime as _dt
import urllib.request
import urllib.error
from typing import Tuple, Optional, List
from kg_schema import KnowledgeNode, DependencyEdge, Provenance


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


_SYSTEM = (
    "你是一名教育知识图谱构建助手。给定课标/教材结构化片段，抽取微知识点候选与依赖边。"
    "只输出 JSON，不输出解释。依赖边(relation=prerequisite)表示 target 的学习必须先掌握 source。"
    "不复制教材原文；只给知识点短标签(<=24字)与课标锚点引用。每个对象必须带 source_ref。"
)

_PROMPT_TMPL = (
    "输出 schema：\n"
    '{"nodes":[{"id":"kp-xxx","label":"...","grade":"小学","std_anchor":"2022课标-数与代数-..."}],'
    '"edges":[{"source":"kp-xxx","target":"kp-yyy","relation":"prerequisite","evidence":"..."}]}\n'
    "输入片段：\n<<INPUT>>\n"
)


def _build_prompt(text: str) -> str:
    return _PROMPT_TMPL.replace("<<INPUT>>", text)


def _parse_llm_json(content: str):
    # 容忍 ```json 代码块包裹
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise ValueError(f"LLM 返回无法解析为 JSON: {content[:200]}")
    return json.loads(m.group(0))


def extract_with_llm(text: str, model: str = "hy3-free",
                     base_url: Optional[str] = None,
                     api_key: Optional[str] = None) -> Tuple[List, List]:
    """真实 LLM 抽取：调用 OpenAI 兼容 /chat/completions。

    环境变量 OPENAI_BASE_URL / OPENAI_API_KEY 可省参；缺失则抛清晰错误（不静默）。
    返回 (nodes, edges)，每条带 Provenance(extraction_method='llm', extraction_model=model)。
    """
    base_url = base_url or os.environ.get("OPENAI_BASE_URL")
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError(
            "extract_with_llm 需要模型 endpoint + key："
            "设环境变量 OPENAI_BASE_URL / OPENAI_API_KEY，或显式传 base_url / api_key。"
        )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _build_prompt(text)},
        ],
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req, timeout=120)
        data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM API 错误 {e.code}: {e.read().decode('utf-8')[:200]}")
    content = data["choices"][0]["message"]["content"]
    obj = _parse_llm_json(content)

    nodes, edges = [], []
    for n in obj.get("nodes", []):
        nodes.append(KnowledgeNode(
            id=n["id"], label=n["label"], grade=n.get("grade"),
            std_anchor=n.get("std_anchor"),
            provenance=Provenance(
                source_ref=n.get("source_ref", ""),
                extraction_method="llm",
                extraction_model=model,
                extracted_at=_now(),
            ),
        ))
    for e in obj.get("edges", []):
        edges.append(DependencyEdge(
            id=f"edge-{e['source']}->{e['target']}",
            source=e["source"], target=e["target"],
            relation=e.get("relation", "prerequisite"),
            provenance=Provenance(
                source_ref=e.get("source_ref", ""),
                extraction_method="llm",
                extraction_model=model,
                extracted_at=_now(),
                evidence=e.get("evidence", ""),
            ),
        ))
    return nodes, edges


def extract_heuristic(text: str, grade: str = "小学") -> Tuple[List, List]:
    """极简离线抽取：按句切分 -> 每句一个候选知识点；按出现顺序生成前序依赖候选。"""
    nodes: List = []
    sentences = [s.strip() for s in re.split(r"[。；;]", text) if len(s.strip()) >= 4]
    edges: List = []
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
