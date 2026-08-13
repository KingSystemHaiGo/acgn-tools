# T002-T2 验证收据（R5 验证执行）

> 实现：长征 Changzheng（R3）｜ 验证：2026-08-13 20:05（本地自检）
> 规格：T002-R2 算法规格完整版（小吉量）+ T001-T1 规则 v0.1（APPROVED commit a55ae46）
> 位置：apps/conflict-detector/conflict_detector.py

## 验证方法
`python3 apps/conflict-detector/conflict_detector.py --self-check`

## 验证结果：12 PASS / 0 FAIL / 共 12 例

### 正控组（应 SUPERSEDED / NO_CONFLICT / REJECTED）
| 用例 | 期望 | 实际 | 判定路径 |
|---|---|---|---|
| T2正控1 (source↔derived 有序更新) | superseded | ✅ PASS | lineage 维度 |
| T2正控2 (est=100/fence=200 vs est=200/live 不相交) | superseded | ✅ PASS | validity 维度 |
| T1-2.2 (血糖条件不重叠) | superseded | ✅ PASS | validity 维度 |
| digest相同-source→derived | superseded | ✅ PASS | lineage 维度（T1 lineage 优先） |
| digest相同-双source | no_conflict | ✅ PASS | digest 维度 |
| T2负控3 (fence 封口收新 derived) | rejected | ✅ PASS | 前置校验 |

### 负控组（应 CONFLICTED）
| 用例 | 期望 | 实际 | 判定路径 |
|---|---|---|---|
| T1-1.1 (华为收入>1000亿 vs ≤1000亿) | conflicted | ✅ PASS | validity 维度（重叠） |
| T1-1.2 (X安全 vs X危险) | conflicted | ✅ PASS | validity 维度（重叠） |
| T2负控1 (双 source digest 不同) | conflicted | ✅ PASS | validity 维度（重叠） |
| T2负控2 (双 derived parent 不同) | conflicted | ✅ PASS | lineage 维度 |
| T1-3.1 (独立来源措辞模糊) | conflicted | ✅ PASS | validity 维度（重叠） |
| 边界组 (同 claim digest 不同 validity 相交) | conflicted | ✅ PASS | validity 维度（重叠） |

## 关键实现决策（与规格的对应）
1. **三维顺序裁决**：lineage 拓扑（维度一）→ digest 语义（维度二）→ validity 重叠（维度三）；lineage 判出即 return 剪枝，与 T1 规则一致。
2. **双 source digest 不同 → 落 validity 裁决**：按 T2-R2 最终判定规则 2，source vs source 无 lineage 关系时进 validity 重叠判定——相交=conflicted（fail-closed 人工仲裁），不相交=superseded。不放维度二直接 fail-closed（否则 T2正控2 会误判）。
3. **fence 封口检查对象=被派生方（parent）**：parent 的 fence 非 null 即封口，拒绝以其为 parent 的新 derived；不是检查派生方自身的 fence。
4. **证据链三元组**：每条 conflicted 输出带 [字段名, 触发修订号(=较新 revision), 双方值]——T4 测试断言可直接消费（断言从「输出含 conflicted」升级到「证据链三元组与预期一致」）。
5. **fail-closed 只在兜底层**：validity 重叠即 conflicted（升格人工仲裁），不自动降级；conflicted 条目只能由用户仲裁（split 四选一出口在 T3 仲裁流程）。

## 待办
- [x] T4 测试门禁接口对齐（R4 契约 detect(entries)->Result）
- [ ] T4 pytest 套件由 R5 双方跑（星星✨ fixture + 本收据对拍）
- [ ] 8/17 checkpoint 演示闭环（T5 集成）

## R4 接口对齐（20:4x 更新，commit e7dcefd 后续）
新增 `detect(entries) -> Result` 契约入口（Result.verdict ∈ {SUPERSEDED,CONFLICTED,REJECTED} + .evidence 列表），
保留 judge_pair/detect_conflicts 供审计。修复两处与 R4 holder fixture 的对齐点：
1. **parent 引用按 entry_id 解析**（R4 fixture 的 parent_claim_id 填的是被派生源 entry_id，如 e-021/e-091）——
   兼容 entry_id 与 claim_id 两套匹配（`_points_to`）。修复后 CONFLICT-003（derived 细化→SUPERSEDED）
   与 CONFLICT-010（fence 封口→REJECTED）不再误判。
2. **split 语义（a177dd1）**：退役祖先（source_role=superseded）+ source 子 claim → 判定 SUPERSEDED 非 conflicted
   （CONFLICT-011），子 claim 为独立 source 非 derived。
3. **证据链对齐 R4 断言**：validity 冲突输出 `["content", rev-N, 双方文本]`；lineage 冲突输出
   `["lineage", rev-N, entryA, entryB]`；修订号为 `rev-N` 字符串——与 R4 fixture 逐字节一致。

**R4 全量 fixture 复跑：11/11 PASS（verdict+evidence 对拍）**
```
001 CONFLICTED / 002 CONFLICTED / 003 SUPERSEDED / 004 SUPERSEDED / 005 CONFLICTED /
006 CONFLICTED / 007 CONFLICTED / 008 REJECTED / 009 REJECTED / 010 REJECTED / 011 SUPERSEDED
```

## 字节级证据（sha256sum，禁手抄）
```
297c8419afcce537516e741d0cd4b7c95161d886ea8de2296afe5664ab5ce1d1  conflict_detector.py
```
