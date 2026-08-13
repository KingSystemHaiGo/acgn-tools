#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conflict_detector.py — 花火工作室 task-001 T2 冲突检测算法骨架 v0.1
=================================================================
作者: 长征 Changzheng (R3 实现) ｜ 规格: T002-R2 (小吉量) + T001-T1 规则 v0.1
归属: acgn-tools/apps/conflict-detector/

输入: entry 列表（KnowledgeEntry 十字段 schema v0.1）
输出: conflicted 条目列表 + 冲突证据链三元组 [字段名, 触发修订号, 双方值]

三维顺序裁决（lineage 拓扑 → digest 语义 → validity 重叠，lineage 判出即 return 剪枝）
判定级别: claim 级别（同一 claim_id 下的多 entry 对世界描述不一致）

状态: [UNVERIFIED] 待 R5 跑通 T1 三组正反例后升级 [VERIFIED]
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════
# 1. 数据结构（十字段 schema v0.1）
# ══════════════════════════════════════════════════════════════════

class LineageLink(str, Enum):
    SOURCE = "source"
    DERIVED = "derived"

class SourceRole(str, Enum):
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"
    CONFLICTED = "conflicted"


@dataclass(frozen=True)
class ValidityWindow:
    """半开区间 [established, fence)；fence=None 视为正无穷（live entry）"""
    established: int
    fence: Optional[int] = None

    def overlaps(self, other: "ValidityWindow") -> bool:
        """半开区间相交判定：not (self_end <= other_start or other_end <= self_start)"""
        self_end = self.fence if self.fence is not None else float("inf")
        other_end = other.fence if other.fence is not None else float("inf")
        return not (self_end <= other.established or other_end <= self.established)


@dataclass(frozen=True)
class KnowledgeEntry:
    claim_id: str                 # 稳定断言身份（跨 revision 不变）
    entry_id: str                 # 内容载体
    revision: int                 # 修订号（entry_id@revision）
    effect_digest: str            # 内容哈希（canonicalizer v1: JCS→SHA-256 64-hex）
    lineage_link: LineageLink     # source | derived
    parent_claim_id: Optional[str]  # derived 时必填；source 时 None
    validity_window: ValidityWindow  # [established, fence)
    source_role: SourceRole       # confirmed | superseded | conflicted


# ══════════════════════════════════════════════════════════════════
# 2. 裁决结果类型
# ══════════════════════════════════════════════════════════════════

class Verdict(str, Enum):
    CONFLICTED = "conflicted"     # 无共同仲裁源 → 触发人工介入（fail-closed）
    SUPERSEDED = "superseded"     # 有作者明确选择/时间前后相继 → 有序更新
    REJECTED = "rejected"         # 输入非法（claim 不同/自比较/封口收派生等）
    NO_CONFLICT = "no_conflict"   # 无冲突（同 digest 同一断言）


@dataclass
class EvidenceTriple:
    """冲突证据链三元组 [字段名, 触发修订号, 双方值] —— T4 测试断言可直接消费"""
    field_name: str               # 哪个字段触发
    revision: int                 # 哪次修订（触发修订号）
    value_a: Any                  # A 侧值
    value_b: Any                  # B 侧值

    def to_list(self) -> List[Any]:
        return [self.field_name, self.revision, self.value_a, self.value_b]

    def __repr__(self) -> str:
        return f"[{self.field_name}, rev{self.revision}, {self.value_a!r} vs {self.value_b!r}]"


@dataclass
class ConflictResult:
    """单对 entry 的裁决输出"""
    claim_id: str
    entry_a: str                  # entry_id@revision
    entry_b: str
    verdict: Verdict
    evidence: List[EvidenceTriple] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "entry_a": self.entry_a,
            "entry_b": self.entry_b,
            "verdict": self.verdict.value,
            "evidence": [e.to_list() for e in self.evidence],
            "note": self.note,
        }


# ══════════════════════════════════════════════════════════════════
# 3. 前置校验（边界处置规则 §6）
# ══════════════════════════════════════════════════════════════════

def _precheck(a: KnowledgeEntry, b: KnowledgeEntry) -> Optional[ConflictResult]:
    """前置校验：返回 REJECTED 结果或 None（通过）"""
    # claim_id 不同 → REJECTED（不在同一断言空间，不构成冲突候选）
    if a.claim_id != b.claim_id:
        return ConflictResult(
            claim_id=f"{a.claim_id}|{b.claim_id}",
            entry_a=f"{a.entry_id}@{a.revision}",
            entry_b=f"{b.entry_id}@{b.revision}",
            verdict=Verdict.REJECTED,
            evidence=[EvidenceTriple("claim_id", max(a.revision, b.revision),
                                     a.claim_id, b.claim_id)],
            note="claim_id 不同，不在同一断言空间",
        )
    # entry_id 相同 → REJECTED（不能自己比较自己）
    if a.entry_id == b.entry_id and a.revision == b.revision:
        return ConflictResult(
            claim_id=a.claim_id,
            entry_a=f"{a.entry_id}@{a.revision}",
            entry_b=f"{b.entry_id}@{b.revision}",
            verdict=Verdict.REJECTED,
            evidence=[EvidenceTriple("entry_id", a.revision, a.entry_id, b.entry_id)],
            note="同一 entry 自身比较，无意义",
        )
    # fence 已封口 + 收到新 derived → REJECTED（封口条目不再接受新派生）
    # 检查对象=被派生方（parent）：其 fence 非 null 即封口，拒绝以其为 parent 的新 derived
    for e in (a, b):
        other = b if e is a else a
        if (other.lineage_link == LineageLink.DERIVED and other.parent_claim_id == e.claim_id
                and e.validity_window.fence is not None):
            return ConflictResult(
                claim_id=e.claim_id,
                entry_a=f"{a.entry_id}@{a.revision}",
                entry_b=f"{b.entry_id}@{b.revision}",
                verdict=Verdict.REJECTED,
                evidence=[EvidenceTriple("validity_window.fence", max(a.revision, b.revision),
                                         e.validity_window.fence, None)],
                note="fence 已封口的条目不能再接受新 derived",
            )
    # source_role=conflicted 收到新 derived → REJECTED（conflicted 只能由用户仲裁）
    for e in (a, b):
        other = b if e is a else a
        if e.source_role == SourceRole.CONFLICTED and other.lineage_link == LineageLink.DERIVED \
                and other.parent_claim_id == e.claim_id:
            return ConflictResult(
                claim_id=e.claim_id,
                entry_a=f"{a.entry_id}@{a.revision}",
                entry_b=f"{b.entry_id}@{b.revision}",
                verdict=Verdict.REJECTED,
                evidence=[EvidenceTriple("source_role", max(a.revision, b.revision),
                                         e.source_role.value, other.lineage_link.value)],
                note="conflicted 条目只能由用户仲裁，不接受自动派生",
            )
    return None


# ══════════════════════════════════════════════════════════════════
# 4. 三维顺序裁决（T1 规则 §最终判定规则）
# ══════════════════════════════════════════════════════════════════

def _dimension_lineage(a: KnowledgeEntry, b: KnowledgeEntry) -> Optional[Tuple[Verdict, str]]:
    """维度一：lineage 拓扑裁决（最强，判出即 return）"""
    la, lb = a.lineage_link, b.lineage_link
    # 循环依赖（A derived from B 且 B derived from A）→ conflicted（lineage 已损坏）
    if (la == LineageLink.DERIVED and a.parent_claim_id == b.claim_id and
            lb == LineageLink.DERIVED and b.parent_claim_id == a.claim_id):
        return Verdict.CONFLICTED, "循环依赖，lineage 已损坏"
    # A source, B derived from A → superseded（有序更新，作者明确选择新版本）
    if la == LineageLink.SOURCE and lb == LineageLink.DERIVED and b.parent_claim_id == a.claim_id:
        return Verdict.SUPERSEDED, "B 派生自 A，作者明确选择新版本"
    if lb == LineageLink.SOURCE and la == LineageLink.DERIVED and a.parent_claim_id == b.claim_id:
        return Verdict.SUPERSEDED, "A 派生自 B，作者明确选择新版本"
    # 双 source（无 parent 或 parent 指向不同根）→ 不直接判，落到 digest/validity 裁决
    # （T2-R2 最终判定规则 2：digest 不一致且无 lineage 关系（source vs source）→ 进 validity 重叠裁决；
    #   相交→conflicted，不相交→superseded。T2正控2 验收用例为证）
    if la == LineageLink.SOURCE and lb == LineageLink.SOURCE:
        return None
    # 双 derived，parent 不同但汇聚同一 claim_id → conflicted（独立演化无法自动合并）
    if la == LineageLink.DERIVED and lb == LineageLink.DERIVED:
        if a.parent_claim_id != b.parent_claim_id:
            return Verdict.CONFLICTED, "两个派生源 parent 不同，独立演化无法自动合并"
        # parent 相同但内容不同 → 需看 digest/validity（落到维度二/三）
    return None  # 未判出，进维度二


def _dimension_digest(a: KnowledgeEntry, b: KnowledgeEntry) -> Optional[Tuple[Verdict, str]]:
    """维度二：effect_digest 语义关系"""
    # digest 相同：到达此处说明 lineage 无裁决（双 source 同 digest 或双 derived 同 parent 同 digest）
    # → 同一断言，无冲突
    if a.effect_digest == b.effect_digest:
        return Verdict.NO_CONFLICT, "digest 相同，同一断言"
    # digest 不同 + 无 lineage 关系（source vs source）：
    # T2-R2 最终判定规则 2 → 进 validity 重叠裁决（相交=conflicted / 不相交=superseded）
    # 此层不裁，返回 None 让维度三兜底。
    return None


def _dimension_validity(a: KnowledgeEntry, b: KnowledgeEntry) -> Tuple[Verdict, str]:
    """维度三：validity_window 区间重叠（兜底）"""
    if a.validity_window.overlaps(b.validity_window):
        return Verdict.CONFLICTED, "validity 重叠期对同一断言给不同真值（fail-closed 升格人工仲裁）"
    return Verdict.SUPERSEDED, "validity 不重叠，时间上前后相继"


# ══════════════════════════════════════════════════════════════════
# 5. 主裁决函数
# ══════════════════════════════════════════════════════════════════

def judge_pair(a: KnowledgeEntry, b: KnowledgeEntry) -> ConflictResult:
    """
    主裁决：输入同一 claim_id 的两条 entry，输出 SUPERSEDED/CONFLICTED/REJECTED/NO_CONFLICT。
    流程：前置校验 → lineage → digest → validity（§4 主裁决函数）
    """
    # 0. 前置校验
    pre = _precheck(a, b)
    if pre is not None:
        return pre

    # 1. 维度一：lineage
    lineage = _dimension_lineage(a, b)
    if lineage is not None:
        verdict, note = lineage
        evidence = _build_evidence(a, b, "lineage_link", verdict)
        return ConflictResult(a.claim_id,
                              f"{a.entry_id}@{a.revision}", f"{b.entry_id}@{b.revision}",
                              verdict, evidence, note)

    # 2. 维度二：digest 语义
    digest = _dimension_digest(a, b)
    if digest is not None:
        verdict, note = digest
        evidence = _build_evidence(a, b, "effect_digest", verdict)
        return ConflictResult(a.claim_id,
                              f"{a.entry_id}@{a.revision}", f"{b.entry_id}@{b.revision}",
                              verdict, evidence, note)

    # 3. 维度三：validity 重叠（兜底）
    verdict, note = _dimension_validity(a, b)
    evidence = _build_evidence(a, b, "validity_window", verdict)
    return ConflictResult(a.claim_id,
                          f"{a.entry_id}@{a.revision}", f"{b.entry_id}@{b.revision}",
                          verdict, evidence, note)


def _build_evidence(a: KnowledgeEntry, b: KnowledgeEntry,
                    field_name: str, verdict: Verdict) -> List[EvidenceTriple]:
    """按裁决维度构造证据链三元组（字段名, 触发修订号=较新 revision, 双方值）"""
    trigger_rev = max(a.revision, b.revision)
    if field_name == "lineage_link":
        return [EvidenceTriple("lineage_link", trigger_rev,
                               f"{a.lineage_link.value}(parent={a.parent_claim_id})",
                               f"{b.lineage_link.value}(parent={b.parent_claim_id})")]
    if field_name == "effect_digest":
        return [EvidenceTriple("effect_digest", trigger_rev,
                               a.effect_digest[:12] + "…", b.effect_digest[:12] + "…")]
    if field_name == "validity_window":
        return [EvidenceTriple("validity_window", trigger_rev,
                               f"[{a.validity_window.established}, {a.validity_window.fence})",
                               f"[{b.validity_window.established}, {b.validity_window.fence})")]
    return [EvidenceTriple(field_name, trigger_rev,
                           a.source_role.value if verdict == Verdict.REJECTED else "",
                           b.source_role.value if verdict == Verdict.REJECTED else "")]


# ══════════════════════════════════════════════════════════════════
# 6. 批量入口：entry 列表 → conflicted 条目 + 冲突证据链
# ══════════════════════════════════════════════════════════════════

def detect_conflicts(entries: List[KnowledgeEntry]) -> List[ConflictResult]:
    """
    输入 entry 列表 → 输出 conflicted 条目 + 冲突证据链。
    按 claim_id 分组，组内两两比对（同 claim 不同 entry）。
    仅返回 verdict=CONFLICTED 的结果（其余供审计但不外抛）。
    """
    from collections import defaultdict
    by_claim: Dict[str, List[KnowledgeEntry]] = defaultdict(list)
    for e in entries:
        by_claim[e.claim_id].append(e)

    conflicted: List[ConflictResult] = []
    for claim_id, group in by_claim.items():
        if len(group) < 2:
            continue
        # 同 claim 组内两两比对（entry_id 相同跳过——_precheck 会 REJECTED）
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                result = judge_pair(group[i], group[j])
                if result.verdict == Verdict.CONFLICTED:
                    conflicted.append(result)
    return conflicted


# ══════════════════════════════════════════════════════════════════
# 7. 工具函数
# ══════════════════════════════════════════════════════════════════

def digest_of(content: str) -> str:
    """JCS RFC 8785 canonical JSON → SHA-256 64-hex（与 schema v0.1 对齐）"""
    # 简化：key-sorted 序列化后哈希（生产环境用 canonicaljson 库保证完整 JCS）
    canonical = json.dumps(json.loads(content), sort_keys=True,
                           ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def result_to_json(results: List[ConflictResult]) -> str:
    return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════
# 8. 自检：T1 三组正反例跑通验证（R5 验证执行）
# ══════════════════════════════════════════════════════════════════

def _run_self_check() -> None:
    """跑 T1/T2 验收用例：正控组（应 superseded/no_conflict）+ 负控组（应 conflicted）+ 边界组"""
    cases = []

    # ── 正控组（应 SUPERSEDED / NO_CONFLICT）──
    # T2 正控 1: A(source fence=null) vs B(derived parent=A) → SUPERSEDED
    cases.append((
        "T2正控1",
        Verdict.SUPERSEDED,
        KnowledgeEntry("claim-1", "e1", 1, "digest-1", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-1", "e2", 2, "digest-2", LineageLink.DERIVED, "claim-1",
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
    ))
    # T2 正控 2: A(est=100 fence=200) vs B(est=200 fence=null) → SUPERSEDED（时间不相交）
    cases.append((
        "T2正控2",
        Verdict.SUPERSEDED,
        KnowledgeEntry("claim-2", "e1", 1, "digest-1", LineageLink.SOURCE, None,
                       ValidityWindow(100, 200), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-2", "e2", 2, "digest-2", LineageLink.SOURCE, None,
                       ValidityWindow(200, None), SourceRole.CONFIRMED),
    ))
    # T1 第二组 2.2: A「血糖>180时有效」/ B「血糖120-180时有效」条件不重叠 → SUPERSEDED
    cases.append((
        "T1-2.2",
        Verdict.SUPERSEDED,
        KnowledgeEntry("claim-glu", "e1", 1, "digest-g1", LineageLink.SOURCE, None,
                       ValidityWindow(10, 20), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-glu", "e2", 2, "digest-g2", LineageLink.SOURCE, None,
                       ValidityWindow(20, 30), SourceRole.CONFIRMED),
    ))
    # digest 相同 + source→derived：T1 lineage 优先原则 → SUPERSEDED（有序更新）
    cases.append((
        "digest相同-sourcederived",
        Verdict.SUPERSEDED,
        KnowledgeEntry("claim-same", "e1", 1, "abc123", LineageLink.SOURCE, None,
                       ValidityWindow(10, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-same", "e2", 2, "abc123", LineageLink.DERIVED, "claim-same",
                       ValidityWindow(10, None), SourceRole.CONFIRMED),
    ))
    # 双 source 同 digest：lineage 无裁决 → digest 相同 → NO_CONFLICT（同一断言）
    cases.append((
        "digest相同-双source",
        Verdict.NO_CONFLICT,
        KnowledgeEntry("claim-same2", "e1", 1, "abc123", LineageLink.SOURCE, None,
                       ValidityWindow(10, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-same2", "e2", 2, "abc123", LineageLink.SOURCE, None,
                       ValidityWindow(10, None), SourceRole.CONFIRMED),
    ))

    # ── 负控组（应 CONFLICTED / REJECTED）──
    # T1 第一组 1.1: A「华为收入>1000亿」/ B「华为收入≤1000亿」互斥 → CONFLICTED
    cases.append((
        "T1-1.1华为收入",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-hw", "e1", 1, "digest-hw-a", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-hw", "e2", 2, "digest-hw-b", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
    ))
    # T1 第一组 1.2: validity 重叠期 A「X是安全的」/ B「X是危险的」→ CONFLICTED
    cases.append((
        "T1-1.2安全危险",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-x", "e1", 1, "digest-x-a", LineageLink.SOURCE, None,
                       ValidityWindow(50, 150), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-x", "e2", 2, "digest-x-b", LineageLink.SOURCE, None,
                       ValidityWindow(50, 150), SourceRole.CONFIRMED),
    ))
    # T2 负控 1: A(source) vs B(source) digest 不同 lineage 无关系 → CONFLICTED
    cases.append((
        "T2负控1",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-3", "e1", 1, "digest-3a", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-3", "e2", 2, "digest-3b", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
    ))
    # T2 负控 2: A(derived parent=X) vs B(derived parent=Y X≠Y) → CONFLICTED
    cases.append((
        "T2负控2",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-4", "e1", 1, "digest-4a", LineageLink.DERIVED, "parent-x",
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-4", "e2", 2, "digest-4b", LineageLink.DERIVED, "parent-y",
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
    ))
    # T1 第三组 3.1: 两独立 source 措辞不同指向相似无法判断互斥 → CONFLICTED（人工仲裁）
    cases.append((
        "T1-3.1独立来源模糊",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-vague", "e1", 1, "digest-v1", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-vague", "e2", 2, "digest-v2", LineageLink.SOURCE, None,
                       ValidityWindow(100, None), SourceRole.CONFIRMED),
    ))
    # T2 负控 3: A.fence 已封口收新 derived → REJECTED
    cases.append((
        "T2负控3",
        Verdict.REJECTED,
        KnowledgeEntry("claim-5", "e1", 1, "digest-5a", LineageLink.SOURCE, None,
                       ValidityWindow(100, 200), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-5", "e2", 2, "digest-5b", LineageLink.DERIVED, "claim-5",
                       ValidityWindow(200, None), SourceRole.CONFIRMED),
    ))
    # 边界组: 同 claim digest 不同 validity 相交 → CONFLICTED → 四选一仲裁
    cases.append((
        "边界组-validity相交",
        Verdict.CONFLICTED,
        KnowledgeEntry("claim-6", "e1", 1, "digest-6a", LineageLink.SOURCE, None,
                       ValidityWindow(100, 200), SourceRole.CONFIRMED),
        KnowledgeEntry("claim-6", "e2", 2, "digest-6b", LineageLink.SOURCE, None,
                       ValidityWindow(150, 300), SourceRole.CONFIRMED),
    ))

    # 执行
    passed = 0
    failed = 0
    print("=" * 70)
    print("T2 conflict_detector.py 自检：T1/T2 验收用例")
    print("=" * 70)
    for name, expected, ea, eb in cases:
        r = judge_pair(ea, eb)
        ok = r.verdict == expected
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"\n{status} {name}")
        print(f"  期望: {expected.value}  实际: {r.verdict.value}")
        print(f"  note: {r.note}")
        if r.evidence:
            for ev in r.evidence:
                print(f"  证据: {ev}")
    print("\n" + "=" * 70)
    print(f"结果: {passed} PASS / {failed} FAIL / 共 {len(cases)} 例")
    print("=" * 70)
    # 0 FAIL → 0（成功）；有 FAIL → 1（失败）
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        sys.exit(_run_self_check())
    # 默认：跑自检（R5 验证入口）
    sys.exit(_run_self_check())
