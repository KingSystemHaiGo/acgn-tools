# R4 测试断言交付：conflict_detector 测试套件 v0.1

作者：星星 ✨（R4 测试断言）｜ 交付 20:05 ｜ 状态：契约先行，待 R3 落地后 R5 验证｜ 归属：T002
输入：T2 算法完整版 19:46 + T4 质量矩阵 v0.1｜ 协作：澄川 R4 断言并行 + 长征 R3 实现 + 小花花 R5 验证执行

## 交付物结构
apps/conflict-detector/：
- **fixtures/**（CONFLICT-001~011 共 11 条）：
  - 001 正控：同 claim 两 source digest 不同 validity 重叠 → CONFLICTED
  - 002 正控：validity 重叠不同真值 → CONFLICTED
  - 003 负控：derived 细化 → SUPERSEDED（lineage 优先）
  - 004 负控：validity 不相交 → SUPERSEDED
  - 005 边界：措辞不同 → 升格 CONFLICTED（fail-closed）
  - 006 边界：语义不明 → CONFLICTED 人工仲裁
  - 007 负控：循环 → CONFLICTED
  - 008 负控：claim 不同 → REJECTED
  - 009 负控：entry 相同 → REJECTED
  - 010 负控：fence 封口 → REJECTED
  - 011 正控：split 最终版 a177dd1 → SUPERSEDED（原 claim 退役 superseded + 新 claim source）
- **tests/test_conflict_detector.py**（pytest 断言套件 14 项测试）

## 矩阵覆盖（T4 v0.1 功能×验证）
- F1×V1 判定正确性必 PASS（001/002 status==CONFLICTED+证据链）
- F1×V2 必 FAIL（003/004 不得误判）
- F2×V1 证据链完整性（001/002/005 三元组逐项比对）
- F3×V2 边界 fail-closed（005/006 不得自动降级 resolve）
- F3×V3 拒绝路径（005/006 升格 CONFLICTED）
- F4×V3 不可逆性（007/008/009/010→REJECTED 或 CONFLICTED）
- F4×V2 split 语义（011 split 最终版→SUPERSEDED）
- F5×V3 lineage 拓扑优先（003/007/011 lineage 优先+split 子 claim 非 derived）
- V4 断言回归（幂等测试）
- V5 断言覆盖（10 用例全在 T1 规则全覆盖）

## 核心纪律（T4 §1.2 落地）
1. **digest 命中≠语义通过**（必须走三维规则裁决后断言输出状态）
2. **双断言模板**（status 语义断言 + evidence 证据链断言）
3. **T2 §5 分歧点处理：split 已按 a177dd1 最终统一版更新**（20:10 小花花通知）——原 claim source_role=superseded（精度不足退役，非被更好版本替代，非 confirmed）+ 新 claim_A/B lineage_link=source（split 创始非派生）+ provenance 注「split from」可追溯；fixture CONFLICT-011 直测此语义，若 R3 实现有出入收据中标注差异

## 接口契约（R3 需实现）
```python
def detect(entries: list[dict]) -> Result:
    # .verdict ∈ {SUPERSEDED, CONFLICTED, REJECTED}
    # + .evidence list[[字段名, 修订号, 值A, 值B]]
```

## 验证收据（待 R5 跑）
```
cd apps/conflict-detector
pytest tests/test_conflict_detector.py -v
sha256sum tests/test_conflict_detector.py fixtures/CONFLICT-*.json
```
字节级收据（sha256sum 输出禁手抄 digest）回传后 → 8/17 与澄川断言三方合流

## 变更记录
- v0.1（20:05）：初始 10 fixture + 12 测试
- v0.1.1（20:15）：split 语义对齐 a177dd1 最终版——新增 CONFLICT-011 + 2 项测试（11 fixture/14 测试）
