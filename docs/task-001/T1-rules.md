# 冲突检测规则 v0.1（conflict_detection_rules.md）

> 作者：小吉量（T001-T1）｜ 交付：2026-08-13 18:27-18:29 ｜ 验收：✅ 通过（18:27）
> 归属：任务包 001 附件区 ｜ 输入：知识条目 schema v0.1 六字段

## 核心问题
同一 claim_id 下两条 entry 的 effect_digest 不同——何时判定「冲突（conflicted）」何时判定「替代（superseded）」？

## 核心原则
conflicted 和 superseded 根本区别 = **「是否有共同作者意图可以仲裁」**。有作者明确选择→superseded；无共同仲裁源→conflicted。**边界案例全部升格为 conflicted，触发人工介入而非自动降级**（fail-closed 哲学）。

## 判定级别：claim 级别
判定在 claim 级别执行。claim_id 是稳定断言身份，是用户看到的「这条知识是什么」的锚点；冲突的本质 = 同一个 claim_id 下存在多个 entry，对世界描述不一致。

## 判定维度一：lineage_link 拓扑
- A 是 source，B 是 derived，且 B.parent_claim_id=A.claim_id → **superseded**（有序更新，作者明确选择新版本）
- A 和 B 都是 source（无 parent，或 parent 指向不同根）→ **conflicted**（两个独立来源对同一断言各执一词，无共同祖先可仲裁）
- A 和 B 都是 derived，parent 不同但最终汇聚到同一 claim_id → **conflicted**（两个派生源汇合前各自独立演化，无法自动合并）
- A 是 derived from B，B 是 derived from A → **conflicted**（循环依赖，lineage 已损坏）

## 判定维度二：effect_digest 语义关系
- digest 不同但内容「更完整的表述」或「勘误」→ **superseded**（新版本明确替代旧版本，作者意图清晰）
- digest 不同且内容「相互排斥的断言」→ **conflicted**（A 声称 P，B 否认 P，或 A 声称 Q∧¬Q）
- digest 不同且内容「互补但不可合并的观测」→ **conflicted**（无共同真值可仲裁，如 A：「X 有用」/B：「X 有害」）
- digest 不同且内容「条件真值」（条件不同）→ **superseded**（B 扩展适用条件，旧 entry 在其条件范围内仍有效）

## 判定维度三：validity_window 区间重叠
- 两个 entry validity_window 不重叠 → **superseded**（时间上前后相继，无同时性冲突）
- 两个 entry validity_window 重叠且 digest 冲突 → **conflicted**（同时对同一断言给不同真值，无时间维可分离）

## 最终判定规则（空段待填）

## 三组验收正反例
### 第一组明确冲突
- 案例 1.1：Entry A「华为收入>1000亿」/ Entry B「华为收入≤1000亿」同一 claim_id 互斥 → **conflicted**
- 案例 1.2：validity 重叠期 A「X是安全的」/ B「X是危险的」→ **conflicted**

### 第二组明确非冲突
- 案例 2.1：Entry B 是 A 的 derived（parent=A）内容为 A 细化（加 n=500，p<0.001）→ **superseded**
- 案例 2.2：A「血糖>180时有效」/ B「血糖120-180时有效」条件不重叠 → **superseded**

### 第三组边界模糊
- 案例 3.1：两独立 source 措辞不同指向相似无法判断互斥 → **conflicted**（触发人工仲裁）
- 案例 3.2：validity 重叠 digest 不同语义关系不明确 → **conflicted**，建议用户对照原文确认

---

## 补充：validity_window 运作规则 + 三组验收正反例（小吉量 18:32 追加）

### validity_window 运作规则
- validity_window 半开区间 [established, fence)：fence=null=live entry 可接受新派生；fence 非 null=已封口，source_role 只能 confirmed→superseded/conflicted 不可逆

### 验收三组正反例
**正控组（应进 confirmed）**：
1. A: lineage=source, source_role=confirmed, fence=null → confirmed ✓
2. A derived from B（B=confirmed），B 未封口 → A.fence=null, source_role=confirmed ✓

**负控组（应进 conflicted/superseded）**：
1. A derived from B / B derived from A（循环）→ lineage_link 构造失败或构造后触发 conflicted ✓
2. A.fence 已封口收到新 derived 请求 → REJECTED（不能再派生）✓
3. A source_role=conflicted 收到新 derived 请求 → REJECTED（conflicted 只能由用户仲裁）✓

**边界组（模糊地带需人工确认）**：
1. A 和 B 同一 claim_id，effect_digest 不同，validity_window 相交但不相等——边界情况，触发 conflicted 或 split ✓
2. lineage_link=derived 但无 parent_claim_id——构造失败，返回 REJECTED ✓
