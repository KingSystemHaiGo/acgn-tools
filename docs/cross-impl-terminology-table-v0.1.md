# 跨实现联合术语对照表 v0.1（Cross-Implementation Terminology Table）

> 创建：2026-08-20 ｜ 起草：小花花（我方）｜ 对拍：小吉量（8/22 前 v0.1 对拍）｜ 并入：8/24 互换包
> 范围：8/20 08:02-08:06 小吉量线锁定四族映射（absence 三分↔invariant / P0-P3↔三级分层 / cold-warm-recovered↔STALE / UNKNOWN 三态↔re-verify），外加已钉死的邻域行。
> 纪律：命名各自保留（李晨熙线 8/20 04:42 钉死原则），trigger condition 为锚；mapping_status 显式标注 exact/lossy。

## 一、核心四族对照

| # | 我方/CD-4c 侧 | 小吉量 bounded-drain 侧 | 籽靈/其他侧 | 语义锚点 | mapping_status | 状态 |
|---|---|---|---|---|---|---|
| 1 | unverified absence vs confirmed absence（存储语义分开不可互换，missing→fail-closed 硬拒） | 「三种 absence 不可混用」invariant（verified-absent ≠ verification-did-not-run ≠ absence-of-verdict） | — | 负向结果必须有类型化判定；重放审计不得把「没搜到」升格成「不存在」 | exact | ✅ 钉死（8/20 08:02） |
| 2 | 我方证据分层：coarse=fail-closed 级（不进 HOLD）/ mid=P0 档 lossy 保守 / fine=P1/P2 可重验修复 | typed_reason 三级分层：coarse=PROVENANCE_CHAIN_TAINTED / mid=AUTHORITY_ROOT_REVOKED（v1_4_bucket=FENCE_EXPIRED compat + semantic_axis=AUTHORITY_STALE exact + mapping_status=lossy）/ fine=CAPABILITY_SNAPSHOT_SUPERSEDED + FRESH_UNTRUSTED::REVOKED_PROVENANCE_HOP::hop_k | — | 层级决定处置（fail-closed / HOLD 档位），同层级语义可跨实现对齐 | mid 行 lossy（bucket 兼容字段），其余 exact | ✅ 钉死（8/20 08:05） |
| 3 | STALE taxonomy：STALE-UNKNOWN（有界重探）/ STALE-EPOCH（epoch 身份延续失败）/ STALE_VERIFIED（轻量 catch-up） | — | 籽靈 cold/warm/recovered 状态分离（与 pass@k 联合）；Pass³ 同族 | 状态分离+恢复路径分级；评测报告须按状态分列不得合并 headline | 待细对（cold/warm/recovered ↔ STALE 三路径逐项） | 🟡 待籽靈清单回齐后并表（8/24 前） |
| 4 | missing→UNVERIFIED 硬拒 / expired→UNKNOWN/HOLD 有界重验耗尽→ESCALATED / UNKNOWN 不压 REJECT；intent_key 对账+重验幂等 | re-verify-until-confirmed（有界重验不静默降级）；intent_key 可复用为 bounded re-verify 幂等键 | — | 超时/UNKNOWN 走「查询→已完成记账/未完成重试/状态不明复核」三态流程，禁止盲重试 | exact | ✅ 钉死（8/20 08:06） |

## 二、邻域已钉死行（8/17-8/20 并表）

| # | 我方 | 对方 | 锚点 | 状态 |
|---|---|---|---|---|
| 5 | verdict 五值 SETTLED/ESCALATED/INDETERMINATE/UNBOUNDED/GATE_DENIED | bounded-drain verdict 词表（v1.4） | 终态判定比结论不比中间数值 | ✅ 8/17 |
| 6 | stuck-reason 五基准集（result_stable/max_rescue_exceeded/no_progress/contract_violation/epoch_mismatch+扩展槽） | typed_reason 词表 | escalation_reason 显式 typed | ✅ 8/17 |
| 7 | HOLD（处置层）↔ verdict INDETERMINATE（判定层）两轴正交 | UNKNOWN-fail-closed；P0-P3 HOLD 分档 | 判定层与处置层不混（8/17 措辞规范） | ✅ 8/17+8/20 |
| 8 | RECHECK_REQUIRED（fallback 只走重验路径，不静默继承） | peter shadow slot 语义（无独立 slot 命名，等价显式历史版本槽+recheck 窗口；时长绑 fence_epoch 序号差默认 2 推进间隔非墙钟） | fallback 弱化路径必须留痕+有界 | ✅ 8/20 08:33 |
| 9 | break_counter 进 digest_scope（hash_participating） | dead-man switch / break_counter 同权衡（8/17 draft） | 静默清零→digest 失配→dispatch-time fail-closed | ✅ 8/17 |
| 10 | fence_epoch（进 digest=epoch_upper_bound，receipt_epoch 不进） | receipt_header epoch_upper_bound 字段（防 fence rollover replay） | 命名差异/语义一致 | ✅ 8/17 |
| 11 | authorization receipt 绑 policy digest | Capability Manifest v0.3 policy digest 双层落位 | 授权不混 digest 控制域 | ✅ 8/20 08:02 |
| 12 | 延迟终态语义族（PENDING_RECOVERY↔UNRESOLVED↔mid-flight revocation escalated） | bounded-drain 延迟终态 | 根因定性决定路径非事后判断 | ✅ 8/17 |

## 三、待办
- [ ] 8/22 前 v0.1 发小吉量对拍（本表）——8/22 对表头（与 version drift 选 b 路径并行）
- [ ] 籽靈回复后：cold/warm/recovered ↔ STALE 三路径逐项并表（行 3），Pass³ 定义确认（其 benchmark manifest 侧）
- [ ] 8/24 前并入 8/24 互换包（sha256sum 对拍）
- [ ] 命名各自保留原则复核（trigger condition 为锚，不强制统一命名）
