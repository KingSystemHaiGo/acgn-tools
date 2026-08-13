# T002-R2：conflict_detector.py 算法逻辑规格

作者：小吉量（R2 规则定义）｜ 交付：2026-08-13 19:44 ｜ 状态：待 R3 代码实现（1/3/4/6 节待补全）｜ 依据：T001-T1 冲突检测规则 v0.1（已 APPROVED commit a55ae46）
代录：CEO 小花花（SPARK_AUTHOR=小吉量）

## 1. 输入数据结构（空段待补）
（六字段怎么进比较函数）

## 2. 三维判定顺序
**默认裁决顺序 lineage（维度一）→ digest 语义（维度二）→ validity 重叠（维度三）**；lineage 裁决优先——若 lineage 拓扑判出 superseded 或 conflicted 直接输出不看后两维

## 3. 各维判定逻辑（空段待补）
- 维度一 lineage 拓扑
- 维度二 digest 语义关系
- 维度三 validity_window 重叠

## 4. 主裁决函数（空段待补）

## 5. split 四选一仲裁出口
verdict=CONFLICTED 时触发人工仲裁四选一（空段待补）；
**split 特殊规则**：split 时原 claim_id 的 source_role→superseded（不再是 live entry）/ 新 claim_A 和新 claim_B 各有独立 claim_id / 原 claim_id 的 validity_window.fence=split_epoch（封口）/ split 是单向操作不可撤销
⚠️ **待核对**：此条与 T1-split-clarification.md（18:57 正式版）表述差异——正式版：父 claim 保持 confirmed 仅封口（frozen 非 replaced）；本规格：父 claim→superseded。需按正式版修正。

## 6. 边界处置规则（空段待补）

## 7. 验收测试用例（R4 断言输入）
**正控组（应判 superseded）**：
1. A(source, fence=null) vs B(derived, parent=A) → SUPERSEDED ✓
2. A(established=100, fence=200) vs B(established=200, fence=null) → SUPERSEDED（时间不相交）✓

**负控组（应判 conflicted）**：
1. A(source) vs B(source 不同 digest lineage 无关系) → CONFLICTED ✓
2. A(derived parent=X) vs B(derived parent=Y X≠Y) → CONFLICTED ✓
3. A.fence 已封口（fence≠null）收到新 derived 请求 → REJECTED ✓

**边界组（应判 conflicted+触发仲裁）**：
1. A 和 B 同一 claim_id digest 不同 validity 相交 → CONFLICTED → 四选一仲裁 ✓
