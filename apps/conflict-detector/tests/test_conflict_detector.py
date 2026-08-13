# R4 测试断言套件：test_conflict_detector.py（测试规格）

作者：星星 ✨（R4 测试断言）｜ 依据：T2 算法完整版 19:46 + T4 质量矩阵 v0.1｜ 协作：澄川 + 长征 + 小花花
核心纪律：digest 命中≠语义通过（digest 不同只是触发必要条件非充分条件，必须走三维规则裁决后断言输出状态）；断言两层=status 语义断言 + evidence 证据链断言
用法：pytest tests/test_conflict_detector.py -v
依赖：conflict_detector.py 暴露 detect(entries) -> Result(verdict, evidence, ...)

> ⚠️ 本文件为星星 ✨ 交付的**测试规格描述版**（20:23 PM 转写入库，[TRANSCRIBED]）——可执行 Python 代码版待确认（若本地为可执行版请发完整代码；否则 R5 阶段按此规格实现）

## 测试 14 项
1. test_conflict_001_positive_conflict（F1×V1+F2×V1：同 claim 两 source digest 不同 validity 重叠→CONFLICTED+证据链）
2. test_conflict_002_positive_overlap（validity 重叠不同真值→CONFLICTED）
3. test_conflict_003_negative_derived（F1×V2+F5×V3：derived 细化→SUPERSEDED lineage 优先不得误判）
4. test_conflict_004_negative_disjoint（validity 不相交→SUPERSEDED）
5. test_conflict_005_boundary_fail_closed（F3×V2+V3：措辞不同→升格 CONFLICTED 不得自动降级）
6. test_conflict_006_boundary_arbitration（语义不明→CONFLICTED 建议人工对照）
7. test_conflict_007_cycle（F4×V3+F5×V3：循环→CONFLICTED）
8. test_conflict_008_claim_mismatch（claim 不同→REJECTED）
9. test_conflict_009_self_compare（entry 相同→REJECTED）
10. test_conflict_010_fence_sealed（fence 封口→REJECTED）
11. test_conflict_011_split_superseded（F4×V2+F5×V3：split 最终版→SUPERSEDED 非 conflicted）
12. test_conflict_011_split_not_derived（F5×V3：split 子 claim 是 source 非 derived，若 R3 误按 derived 暴露差异）
13. test_matrix_v5_coverage（V5 覆盖 11 条全在）
14. test_matrix_v4_idempotency（V4 幂等正/负/边界各一）

## 辅助函数
- load_fixtures（加载全部）
- run_detector（R3 未落地时 pytest.skip）
- assert_verdict（status 语义断言）
- assert_evidence（evidence 逐项比对）
- assert_no_auto_resolve（fail-closed 断言）
- assert_idempotent（幂等断言）

## 完整 sha256 收据（星星 ✨ 20:23 提供，64 hex 全文 12 文件）
- README-R4.md = e87cfb33c34dfc6a0e2d2c5b50f7c94a9c5addd3be096d45298e8db0bcd96c97
- CONFLICT-001 = 7eef995075c33ba6649266bcdfd050732a70d1a57ced443905bf32d59ec754dc
- CONFLICT-002 = bcf64724cdffa947a1586451033f98e346f8b14cea6d2da79b0c991bd7dbfb4f
- CONFLICT-003 = b0fb2aff0978efdc7693ea8fab7ba1a28e7f0fda88dd1498cfa42ddb8c3fdc5b
- CONFLICT-004 = 0eaa4ee8381ff79303847f7cbb5de9701e989df0ce3f2fd8dc14ddc02bf74536
- CONFLICT-005 = dae3398136a72ca14864e38272cd9cf1537cdfd46cacb28a0a1c350cb29bea1c
- CONFLICT-006 = 7b8d243d9886bb3b9a30c631cab75befede745ab41ff49e29ecda786125fc9a9
- CONFLICT-007 = 5258d26ebdc417078b74049889b66269b5c9b30fd49154ddf1941a319ed53ab8
- CONFLICT-008 = 9cfa883515e1f9d4d29cce9b25f3f03635f6576850158ff9966631e56ea7c5eb
- CONFLICT-009 = 53d7804a7663615acc8822948fcbbf31ed739130d6a962c51765f5d7d1a72340
- CONFLICT-011 = 5a460628b7d1c8741575c16a5750b8db1a61b4a7906865b1d3221c1cc29de0dc
- tests/test_conflict_detector.py = 6c315cd2c1511cde97adc710e2043bcd20261e6883d05e4d98d51c540332402b
- （注：CONFLICT-010 未列入 12 文件清单——v0.1 收据已有其哈希，请补 64 hex 确认）

## split 预期确认（按最终版 a177dd1）
- CONFLICT-011 = split 正控（原 claim superseded 退役+子 A/B lineage=source+provenance split from→预期 SUPERSEDED）
- CONFLICT-010 = 非 split 场景（rejected 对照组不受影响）
- 其余 001-009 无 split 场景
