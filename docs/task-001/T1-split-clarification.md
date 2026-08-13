# T1 补充：split（分叉）概念的正式定义与边界澄清

> 作者：小吉量（T001-T1）｜ 交付：2026-08-13 18:57 ｜ 代录：CEO 小花花（代提交方案 a）
> 归属：任务包 001 附件区 ｜ 关联：docs/task-001/T1-rules.md（18:40/18:55 split 澄清的正式版）

## 核心定义（19:54 最终统一表述）
split（分叉）= 同一 claim_id 下 entry 拆出多个子 claim。原 claim_id → source_role=**superseded（精度不足退役，非被更好版本替代）**；新 claim_A+新 claim_B → lineage_link=**source（各自独立，split 是创始行为而非派生）**；新 claim provenance 注「split from [原 claim_id]」（audit trail 可追溯）。

## split vs superseded 区别（最终统一）
- **superseded（常规）** = 同一断言的替代，父变 superseded（被更好版本替换）
- **superseded（split 退役）** = 精度不足退役，不等于「被谁替代」；两句话可并存的正确解读：
  - 「父不替代」= split 后原 claim 不再生效（精度不够），不是被替换成更好版本
  - 「source_role→superseded」= 退役，不等于「被谁替代」
- **split** = 分区创始：原 claim 退役（frozen 效果）+ 新 claim 独立 source

## split 三要素（最终统一）
1. 原 claim_id → source_role=superseded（精度不足退役，不再接受新派生）
2. 新 claim_A/B → lineage_link=source（各自独立，split 是创始行为而非派生）
3. 新 claim_A/B provenance 注「split from [原 claim_id]」（audit trail 可追溯）

## 运作规则（三条）
1. **split 单向不可撤销**（一旦 split，父封口子 claim 独立演化，无反向合并回父）
2. **父 entry 封口后不参与冲突检测**（fence 非 null=冻结，不再接受新派生/不再进冲突判定域）
3. **split 不规避冲突**——子 claim 之间若互斥仍升格 conflicted（split 只是分区不是消解，矛盾在子层继续存在则继续诚实标注）

## 完整 lineage 四状态对照表
| 状态 | 含义 | 父 claim 状态 | 子 claim | 冲突检测参与 |
|---|---|---|---|---|
| source | 原创根节点 | — | — | 是 |
| derived | 派生（带 parent_claim_id） | confirmed（未封口） | 单链派生 | 是 |
| split | 分叉（fence_epoch 拆分） | superseded（退役 frozen，精度不足非被替代） | 多子 claim 各独立 claim_id+lineage=source+provenance split from | 父不参与/子参与 |
| 无关系 | 独立条目 | — | — | 是（跨 claim 冲突判定） |

## 判定规则（IF-THEN）
- IF 同一 claim_id 下 entry 拆分为多个子 claim AND 父内容仍有效 → split（父 confirmed+封口）
- IF 同一 claim_id 下新 entry 替代旧 entry AND 同一断言 → superseded（父变 superseded）
- IF 子 claim 之间互斥 → 仍 conflicted（split 不消解矛盾）
- IF 父 entry 已封口（fence 非 null）→ 不参与冲突检测
