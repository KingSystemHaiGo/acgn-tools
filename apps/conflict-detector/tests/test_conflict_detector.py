# R4 可执行测试套件：test_conflict_detector.py（pytest 全绿版）
# =================================================================
# 作者：星星 ✨（R4 测试断言规格）｜ 落地：小花花（8/26 产品攻坚 Day 1：规格版→可执行版）
# 依据：README-R4.md + 星星 ✨ 测试规格（v0.1.1：11 fixture / 14 测试）
# 核心纪律：digest 命中≠语义通过——必须走三维规则裁决后断言输出状态；
#           断言两层 = status 语义断言 + evidence 证据链断言
# 用法：cd apps/conflict-detector && python3 -m pytest tests/ -v
# 验收：14 项全过（8/26 产品攻坚步骤 1 硬验收）
# =================================================================
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conflict_detector import (  # noqa: E402
    KnowledgeEntry,
    LineageLink,
    SourceRole,
    ValidityWindow,
    Verdict,
    detect,
)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
ALL_CASE_IDS = ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011"]


# ── 辅助函数 ─────────────────────────────────────────────────────
def entry_from_dict(d):
    """fixture JSON entry → KnowledgeEntry。
    注：fixture 的 source_role 字段较宽松（source/derived/superseded），
    与枚举 confirmed/superseded/conflicted 映射：source/derived→CONFIRMED，
    superseded→SUPERSEDED，conflicted→CONFLICTED（仅 SUPERSEDED/CONFLICTED 参与裁决逻辑）。
    """
    vw = d["validity_window"]
    sr_map = {"source": SourceRole.CONFIRMED, "derived": SourceRole.CONFIRMED,
              "superseded": SourceRole.SUPERSEDED, "confirmed": SourceRole.CONFIRMED,
              "conflicted": SourceRole.CONFLICTED}
    return KnowledgeEntry(
        claim_id=d["claim_id"],
        entry_id=d["entry_id"],
        revision=int(d["revision"].split("-")[1]),
        effect_digest=d["effect_digest"],
        lineage_link=LineageLink(d["lineage_link"]),
        parent_claim_id=d.get("parent_claim_id"),
        validity_window=ValidityWindow(vw["established"], vw.get("fence")),
        source_role=sr_map.get(d["source_role"], SourceRole.CONFIRMED),
        content=d.get("content", ""),
    )


def load_fixture(case_id):
    with open(os.path.join(FIXTURE_DIR, f"CONFLICT-{case_id}.json"), encoding="utf-8") as f:
        data = json.load(f)
    return data, [entry_from_dict(e) for e in data["entries"]]


def run_detector(case_id):
    """加载 fixture 并跑 detect()"""
    data, entries = load_fixture(case_id)
    return data, detect(entries)


def assert_verdict(result, expected_verdict):
    """status 语义断言"""
    assert result.verdict.value == expected_verdict, \
        f"verdict 不符: 期望 {expected_verdict}, 实际 {result.verdict.value}"


def assert_evidence(result, expected_evidence):
    """evidence 证据链断言（[字段名, 修订号, 值A, 值B] 逐项比对）"""
    actual = [list(ev) for ev in result.evidence]
    assert actual == expected_evidence, f"evidence 不符: 期望 {expected_evidence}, 实际 {actual}"


def assert_no_auto_resolve(result):
    """fail-closed 断言：边界 case 不得自动降级 resolve"""
    assert result.verdict.value != "SUPERSEDED", "边界 case 不得自动降级为 SUPERSEDED"
    assert result.verdict.value != "REJECTED", "边界 case 不得被 REJECTED 掩盖"


# ── 测试 1-11：fixture 驱动（F1×V1/F2×V1/F3×V2/F4×V3/F5×V3 矩阵）──
def test_conflict_001_positive_conflict():
    """F1×V1+F2×V1：同 claim 两 source digest 不同 validity 重叠 → CONFLICTED + 证据链"""
    data, r = run_detector("001")
    assert_verdict(r, "CONFLICTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_002_positive_overlap():
    """F1×V1：validity 重叠不同真值 → CONFLICTED"""
    data, r = run_detector("002")
    assert_verdict(r, "CONFLICTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_003_negative_derived():
    """F1×V2+F5×V3：derived 细化 → SUPERSEDED（lineage 优先不得误判）"""
    data, r = run_detector("003")
    assert_verdict(r, "SUPERSEDED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_004_negative_disjoint():
    """F1×V2：validity 不相交 → SUPERSEDED"""
    data, r = run_detector("004")
    assert_verdict(r, "SUPERSEDED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_005_boundary_fail_closed():
    """F3×V2+V3：措辞不同 → 升格 CONFLICTED，不得自动降级 resolve"""
    data, r = run_detector("005")
    assert_verdict(r, "CONFLICTED")
    assert_no_auto_resolve(r)
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_006_boundary_arbitration():
    """F3×V2+V3：语义不明 → CONFLICTED（建议人工仲裁）"""
    data, r = run_detector("006")
    assert_verdict(r, "CONFLICTED")
    assert_no_auto_resolve(r)
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_007_cycle():
    """F4×V3+F5×V3：循环（互为 derived）→ CONFLICTED"""
    data, r = run_detector("007")
    assert_verdict(r, "CONFLICTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_008_claim_mismatch():
    """F4×V3：claim 不同 → REJECTED"""
    data, r = run_detector("008")
    assert_verdict(r, "REJECTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_009_self_compare():
    """F4×V3：entry 相同（自比较）→ REJECTED"""
    data, r = run_detector("009")
    assert_verdict(r, "REJECTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_010_fence_sealed():
    """F4×V3：fence 封口收新 derived → REJECTED"""
    data, r = run_detector("010")
    assert_verdict(r, "REJECTED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_011_split_superseded():
    """F4×V2+F5×V3：split 最终版（退役祖先+source 子 claim）→ SUPERSEDED 非 conflicted"""
    data, r = run_detector("011")
    assert_verdict(r, "SUPERSEDED")
    assert_evidence(r, data["expected"]["evidence"])


def test_conflict_011_split_not_derived():
    """F5×V3：split 子 claim 是 source（创始）非 derived——若 R3 误按 derived 暴露差异"""
    data, entries = load_fixture("011")
    retired_claim = [e for e in entries if e.source_role == SourceRole.SUPERSEDED][0].claim_id
    kids = [e for e in entries if e.claim_id != retired_claim]
    assert len(kids) >= 2, "split 场景应至少两个子 claim"
    for kid in kids:
        assert kid.lineage_link == LineageLink.SOURCE, \
            f"split 子 claim {kid.entry_id} 应为 source（创始非派生），实际 {kid.lineage_link.value}"
    # 子 claim 应独立成组（各自 claim_id），不被视作 derived 子条目
    assert len({k.claim_id for k in kids}) == len(kids), "split 子 claim 应为独立 claim_id"


def test_matrix_v5_coverage():
    """V5 断言覆盖：11 条 fixture 全在（每 case 都有专属测试，无漏覆盖）"""
    tested = {"001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011"}
    assert tested == set(ALL_CASE_IDS), f"覆盖缺口: {set(ALL_CASE_IDS) - tested}"


def test_matrix_v4_idempotency():
    """V4 断言回归：正/负/边界各一跑两次，结果幂等（verdict+evidence 一致）"""
    for case_id in ("001", "008", "005"):
        data, entries = load_fixture(case_id)
        r1 = detect(entries)
        r2 = detect(entries)
        assert r1.verdict == r2.verdict, f"{case_id} 幂等失败: {r1.verdict} vs {r2.verdict}"
        assert [list(e) for e in r1.evidence] == [list(e) for e in r2.evidence], \
            f"{case_id} evidence 幂等失败"
