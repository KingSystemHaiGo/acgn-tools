# T1 补充：split（分叉）概念的正式定义与边界澄清

> 作者：小吉量（T001-T1）｜ 交付：2026-08-13 18:57 ｜ 代录：CEO 小花花（代提交方案 a）
> 归属：任务包 001 附件区 ｜ 关联：docs/task-001/T1-rules.md（18:40/18:55 split 澄清的正式版）

## 核心定义
split（分叉）= 同一 claim_id 下 entry 拆出多个子 claim，父 claim 不被替代（source_role 保持 confirmed，validity_window.fence 封口）。

## split vs superseded 区别
- **superseded** = 同一断言的替代，父变 superseded
- **split** = 不同断言的分区，父保持 confirmed（封口但内容不变）

## split 四要素
1. 父 entry 封口不替代
2. 子 claim 独立 claim_id
3. lineage_link=derived
4. source_role=confirmed

## 运作规则（三条）
1. **split 单向不可撤销**（一旦 split，父封口子 claim 独立演化，无反向合并回父）
2. **父 entry 封口后不参与冲突检测**（fence 非 null=冻结，不再接受新派生/不再进冲突判定域）
3. **split 不规避冲突**——子 claim 之间若互斥仍升格 conflicted（split 只是分区不是消解，矛盾在子层继续存在则继续诚实标注）

## 完整 lineage 四状态对照表
| 状态 | 含义 | 父 claim 状态 | 子 claim | 冲突检测参与 |
|---|---|---|---|---|
| source | 原创根节点 | — | — | 是 |
| derived | 派生（带 parent_claim_id） | confirmed（未封口） | 单链派生 | 是 |
| split | 分叉（fence_epoch 拆分） | confirmed（封口 frozen） | 多子 claim 各独立 claim_id | 父不参与/子参与 |
| 无关系 | 独立条目 | — | — | 是（跨 claim 冲突判定） |

## 判定规则（IF-THEN）
- IF 同一 claim_id 下 entry 拆分为多个子 claim AND 父内容仍有效 → split（父 confirmed+封口）
- IF 同一 claim_id 下新 entry 替代旧 entry AND 同一断言 → superseded（父变 superseded）
- IF 子 claim 之间互斥 → 仍 conflicted（split 不消解矛盾）
- IF 父 entry 已封口（fence 非 null）→ 不参与冲突检测
