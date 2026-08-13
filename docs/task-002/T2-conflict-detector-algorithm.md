# T002-R2：conflict_detector.py 算法逻辑规格（完整版）

作者：小吉量（R2 规则定义）｜ 交付：2026-08-13 19:44（完整版 19:46）｜ 状态：待 R3 代码实现｜ 依据：T001-T1 冲突检测规则 v0.1（已 APPROVED commit a55ae46）
代录：CEO 小花花（SPARK_AUTHOR=小吉量）｜ 更新：覆盖 c5f6091 框架版

## 1. 输入数据结构
十字段：claim_id / entry_id / revision / effect_digest / lineage_link / parent_claim_id / validity_window / established / fence / source_role——对应 KnowledgeEntry 类

## 2. 三维判定顺序
默认裁决顺序 lineage（维度一）→ digest 语义（维度二）→ validity 重叠（维度三）；lineage 裁决优先——判出 superseded 或 conflicted 直接输出不看后两维

## 3. 各维判定逻辑
- **维度一 lineage**：A source B derived from A → SUPERSEDED；A/B 都 source → CONFLICTED（无共同祖先）；都 derived parent 不同汇聚同 claim_id → CONFLICTED（独立演化）；循环依赖 → CONFLICTED；其他 → 看维度二
- **维度二 digest**：相同 → 无需裁决（同一断言）；不同 → 需 content 语义分析，自动化系统建议升格 CONFLICTED 由人工仲裁
- **维度三 validity**：半开区间 [established, fence)，fence=None 视为正无穷；不相交（a_end<=b_start 或 b_end<=a_start）→ SUPERSEDED（时间前后相继）；相交 → CONFLICTED（同时窗不同真值）

## 4. 主裁决函数
输入 entry_a/entry_b（同一 claim_id）；输出 SUPERSEDED/CONFLICTED/REJECTED；
流程：
1. 前置：claim_id 相同 entry_id 不同 → 否则 REJECTED
2. lineage 裁决 → 有则返回
3. digest 语义裁决 → 有则返回
4. validity 重叠裁决 → 返回

## 5. split 四选一仲裁出口（最终统一版 19:54）
verdict=CONFLICTED 触发人工仲裁四选一：
- **KEEP_A_SUPERSEDE_B**：保留 A，B source_role→superseded（A 被 B 替代）
- **KEEP_B_SUPERSEDE_A**：保留 B，A source_role→superseded（B 被 A 替代）
- **SPLIT**：原 claim_id → source_role=**superseded（精度不足退役，非被更好版本替代）**；新 claim_A+新 claim_B → lineage_link=**source（各自独立，split 是创始行为而非派生）**；provenance 注「split from [原 claim_id]」；原 validity_window.fence=split_epoch（退役 frozen 效果）
- **REDEFINE**：重新定义 claim
**最终统一解读（化解「不替代」与「superseded」矛盾）**：「父不替代」= split 后原 claim 不再生效（精度不够），不是被替换成更好版本；「source_role→superseded」= 退役，不等于「被谁替代」。
split 特殊规则：新 claim_A/B 各有独立 claim_id+lineage=source；原 validity_window.fence=split_epoch；split 单向不可撤销

## 6. 边界处置规则
- claim_id 不同 → REJECTED
- entry_id 相同 → REJECTED（不能自己比较）
- fence 封口收新 derived → REJECTED
- source_role=conflicted 收新 derived → REJECTED（只能用户仲裁）

## 7. 验收测试用例
**正控组**：
1. A(source fence=null) vs B(derived parent=A) → SUPERSEDED ✓
2. A(est=100 fence=200) vs B(est=200 fence=null) → SUPERSEDED（时间不相交）✓

**负控组**：
1. A(source) vs B(source digest 不同 lineage 无关系) → CONFLICTED ✓
2. A(derived parent=X) vs B(derived parent=Y X≠Y) → CONFLICTED ✓
3. A.fence 已封口收新 derived → REJECTED ✓

**边界组**：
1. 同 claim digest 不同 validity 相交 → CONFLICTED → 四选一仲裁 ✓
