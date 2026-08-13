# T4 测试门禁：质量矩阵（功能×验证）v0.1

作者：星星 ✨（质量/矩阵，T001-T4）｜ 交付：2026-08-13 18:57 ｜ 状态：草案（待 T2 算法落地后对拍）｜ 归属：任务包 001
输入：T1 三组正反例 + T2 证据链三元组规范 + 质量矩阵「功能×验证」
协作：澄川（测试断言）写「每条用例必 FAIL/必 PASS 断言」，我做「质量矩阵覆盖每条测试用例」——一守承诺，一可勾选可对拍可回归

## 1. 质量矩阵框架：功能×验证
质量不是「有没有测试」而是每个功能点都有对应验证维度；矩阵化=断言 digest≠语义通过。

### 1.1 矩阵结构
每条测试用例占一格（功能维度×验证维度）：
- F1 判定正确性（同 claim 三态判定）→ V1 断言必 PASS（正例命中）
- F2 证据链完整性（conflicted 带 [字段名,触发修订号,双方值] 三元组）→ V2 断言必 FAIL（反例必不误判）
- F3 边界 fail-closed（模糊升格 conflicted 不自动 resolve）→ V3 断言拒绝（REJECTED 路径）
- F4 不可逆性（conflicted 只能用户仲裁）→ V4 断言回归（重复运行幂等）
- F5 lineage 拓扑裁决优先（三维顺序）→ V5 断言覆盖（每条规则至少 1 用例）

矩阵格=功能×验证，如 F2×V1。

### 1.2 断言 digest≠语义通过（核心纪律）
digest 命中≠语义通过——两条 entry digest 不同只是「触发检测」必要条件非「判定 conflicted」充分条件，必须走三维规则裁决后断言输出状态。
断言模板（澄川可消费）：status 语义断言 + evidence 证据链断言。

## 2. 矩阵覆盖表（T1 三组正反例+边界）
- **正例组**（F1×V1+F2×V1）：CONFLICT-001-正例（华为收入互斥→conflicted）/ CONFLICT-002-正例（X 安全 vs 危险 validity 重叠→conflicted）
- **负例组**（F1×V2）：CONFLICT-003-反例（derived 细化→superseded 必 FAIL 不误判 conflicted）/ CONFLICT-004-反例（血糖条件不重叠→superseded）
- **边界组**（F3×V2+F3×V3）：CONFLICT-005-边界（独立 source 措辞相似→升格 conflicted 人工仲裁）/ CONFLICT-006-边界（validity 重叠语义不明→conflicted 建议对照原文）
- **负控/不可逆组**（F4×V3+F5×V3）：CONFLICT-007-负控（循环依赖→conflicted/REJECTED）/ CONFLICT-008-负控（fence 封口收 derived→REJECTED）/ CONFLICT-009-负控（conflicted 收 derived→REJECTED 只能用户仲裁）/ CONFLICT-010-负控（derived 无 parent→构造失败 REJECTED）

## 3. 验证维度细化
- V1 必 PASS（正例 2 条）
- V2 必 FAIL（负例+边界 4 条）
- V3 断言拒绝（负控 4 条）
- V4 断言回归（10 条+快照）
- V5 断言覆盖（T1 每规则≥1 用例）

## 4. T1 规则覆盖表（V5）——11 行
1. lineage derived→superseded（003）
2. lineage 两 source→conflicted（001）
3. lineage 循环→conflicted/REJECTED（007）
4. digest 互斥→conflicted（001）
5. digest 完整→superseded（003）
6. digest 条件真值→superseded（004）
7. validity 重叠冲突→conflicted（002/006）
8. validity 不重叠→superseded（004）
9. 三维顺序 lineage 判出后两维不看（003/007）
10. 边界 fail-closed（005/006）
11. conflicted 不可自动 resolve（008/009）

## 5. 验收自检
- 矩阵覆盖每条用例 ✅（10 条全在格）
- 每条用例有断言方向 ✅
- 覆盖 conflicted 不自动 resolve ✅
- digest≠语义纪律 ✅
- T1 规则全覆盖 ✅（11 行）
- 待 T2 落地后跑通 10 条 fixture 回传字节级收据 ⏳
- 待澄川断言合流 ⏳

## 6. 协作契约（对澄川）
- 澄川把 §2 每条用例写成可执行断言（必 PASS/必 FAIL/必 REJECTED）
- 星星负责矩阵结构+规则覆盖+digest≠语义纪律，矩阵覆盖每条测试用例=验收口径
- 8/17 checkpoint 合流=矩阵+断言+T2 算法三方对拍
