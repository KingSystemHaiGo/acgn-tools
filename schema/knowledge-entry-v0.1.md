# 花火工作室技术预研（Tech Prelim v0.1）

> 启动：2026-08-13 17:53（排期纠偏后并行启动）｜ 目标：产品技术骨架 v0.1（8/17 前）

## 并行原则（小吉量 17:53 表述，采纳）
- 对拍收束 = 验证语言鲁棒性；schema 预研 = 把语言投影到产品界面——互为输入输出，不互抢时间
- 8/17 = checkpoint（外部可见进度锚点），非开工日/终点；对拍收束是内部验证，两者职责不同

## 知识条目 schema v0.1（六字段完整版，小吉量 17:54 补全）
1. **claim_id**：稳定断言身份（跨 revision 不变）——one-atom-one-claim
2. **entry_id@revision**：可演化内容载体（重分块/合并不改变 claim_id 锚点）——内容与身份分离
3. **effect_digest**：内容哈希，锚定「当时允许采哪些 token」的 allowed set（↔canonicalizer v1）
4. **lineage_link**：source | derived，携带 parent claim_id（溯源指针，原创 vs 派生）（↔parent_digest_ref 血缘）
5. **validity_window**：bounded-drain epoch 范围 [established, fence)（↔半开区间）
6. **source_role**：confirmed | superseded | conflicted（知识条目三元状态：confirmed=有效确认/superseded=被后续版本替代/conflicted=同 claim_id 冲突无法自动 reconciliation）（↔evidence 三态+CONFLICTED 折叠）

六字段=「可验证引用图谱」产品骨架语言：是什么（claim）/从哪来（lineage）/状态如何（role）/何时有效（window）/内容是什么（digest）/怎么演化（revision）

## 关联
- 产品核心产出：可验证引用图谱（非摘要）——调研样本 #1 小吉量 Q2
- 留存引擎：冲突检测（CONFLICTED）——两样本 Q3 收敛
- 价值主张：暴露矛盾而非存储 + 知识不会悄悄过期
- MVP 体验原则：被认真对待/追问不落空/诚实不确定（Castorice）

## v0.1 技术注释（小吉量 18:04 全文交付）

### 设计目标
「可验证引用图谱」的产品骨架语言，让用户回答：这条知识是什么（claim）/从哪来（lineage）/现在状态如何（source_role）/什么时候有效（validity_window）/内容是什么（effect_digest）/怎么演化（entry_id@revision）

### 六字段定义
1. **claim_id**: string——稳定断言身份，跨 revision 不变；对应 bounded-drain 的 intent_hash；生成=JCS RFC 8785(claim_text)→SHA-256 64-hex
2. **entry_id@revision**: string——可演化内容载体，格式 entry_id+@+revision_counter；重分块/合并不改变 claim_id 锚点；entry_id 每次内容更新时递增
3. **effect_digest**: string——内容哈希，锚定 allowed set（canonicalizer v1）；对应 bounded-drain 的 effect_digest；生成=JCS(content_text)→SHA-256 64-hex
4. **lineage_link**: enum {source, derived}——source=原创/derived=派生；若 derived 须携带 parent_claim_id；支持 audit trail 重建
5. **validity_window**: object——established: uint64（epoch）/fence: uint64|null（null=未封口仍 live）；半开区间 [established, fence)；fence 非 null 时该条目不再接受新派生
6. **source_role**: enum {confirmed, superseded, conflicted}——confirmed=有效确认（fence 已封口）/superseded=被后续版本替代/conflicted=同 claim_id 冲突无法自动 reconciliation 触发用户介入提示

### 与 bounded-drain receipt 对应
- claim_id ↔ intent_hash
- effect_digest ↔ effect_digest（canonicalizer v1）
- validity_window ↔ epoch 半开区间 [established, fence)
- source_role ↔ evidence 三态+CONFLICTED（confirmed/superseded/conflicted）
- lineage_link ↔ parent_digest_ref 血缘
- entry_id@revision ↔ 内容与身份分离（SUPERSEDE 不破坏锚）

### 运作规则（v0.1）
- claim_id 是唯一稳定身份，贯穿条目全生命周期
- effect_digest 变更 → 新 entry_id@revision，claim_id 不变
- lineage_link=derived 时须提供 parent_claim_id，不可闭环
- validity_window.fence 封口后 source_role 只能从 confirmed → superseded/conflicted，不可逆
- conflicted 条目在用户明确仲裁前不自动 resolve

### 与 bounded-drain receipt 对应关系
| Knowledge Entry | Bounded-drain Receipt |
|---|---|
| claim_id | intent_hash |
| entry_id@revision | effect_sequence |
| effect_digest | effect_digest（同构） |
| lineage_link | lineage_link |
| validity_window | [established_epoch, fence_epoch) |
| source_role | effect_state |

### v0.1 已知局限（v0.2 候选）
- 不含 policy_version 字段（v0.2 加入）
- 不含 authority label（v0.2 加入）
- 不含 cross-reference receipt ID（v0.2 加入）
- source_role=conflicted 时用户仲裁流程未定（待用户调研结果）
