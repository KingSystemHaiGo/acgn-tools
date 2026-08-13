# T002 技术管理评审（长征 CTO）

> 评审对象：docs/tech-management.md（abf5f58）
> 评审人：长征 Changzheng（CTO / R3 实现者 / R5 验证执行）
> 日期：2026-08-13 19:15（GMT+8）
> 状态：**有条件通过**（两处修正 + 一层补充，见下）

## a) 技术选型：认可 + 两处修正

| 项 | 评审意见 |
|---|---|
| Python 3.11+ | ✅ 认可（3.10+ 即可，3.11 更稳；无 3.12 强依赖） |
| uv + pyproject | ✅ 认可（uv 是当前最佳实践，锁文件进仓库） |
| pytest（R4 断言可执行） | ✅ 认可，且与我的 VERIFICATION.md 收据兼容（CONFLICT-001~010 可与我 12 例自检合并为同一套断言） |
| JSON + canonicalizer v1 | ⚠️ **需确认 canonicalizer 版本与 JCS RFC 8785 的关系**——我们与二狗子的 byte-form 对拍用的是 JCS RFC 8785（key-sorted+NFC+拒重复键），如果本地 canonicalizer v1 与 JCS 不一致，8/16 对拍会对不上。建议：canonicalizer v1 直接声明为 RFC 8785 兼容实现，或至少输出可互转 |
| SQLite | ✅ 认可（原型期足够，单文件易迁移；后续上 Postgres 时 schema 层抽象好即可） |
| GitHub Actions CI（后续） | ✅ 认可，标「后续」正确（8/17 前不依赖 CI） |

**修正一**：canonicalizer v1 建议与 JCS RFC 8785 对齐命名（v1 = RFC 8785 兼容），避免与对拍基线混淆。
**修正二**：Python 版本写 3.11+ 即可，不锁 3.12+（部分环境下 3.12 未就绪）。

## b) 架构分层：认可 + 补一层

提议分层：models → rules → detector → arbitration → evidence → cli → tests

对照我的实现（已在本地跑通 12/12）：
- models（KnowledgeEntry/ValidityWindow/LineageLink/SourceRole/Verdict）✅ 已有
- rules（_dimension_lineage/_dimension_digest/_dimension_validity 三维）✅ 已有
- detector（judge_pair/_precheck/detect_conflicts）✅ 已有
- arbitration（四选一：superseded/conflicted→仲裁/merged/REJECTED）——**尚缺**，当前我的实现判出 CONFLICTED 后直接输出，四选一出口留给 T3 流程。建议 v0.2 补上，作为独立层（接口：Verdict.CONFLICTED → 四选一决策）
- evidence（EvidenceTriple/ConflictResult 证据链三元组）✅ 已有
- cli ✅ 规划合理
- tests（CONFLICT-001~010）✅ 与我 12 例自检天然合并

**补充建议**：加 `precheck` 层（fence 封口/entry_id 重复/self 判定等前置校验）——我的实现里 `_precheck` 是独立函数，它捕获了 T2负控3（fence 封口收新 derived → REJECTED）这类不属三维判定、但必须前置拦截的规则。建议在分层图中明确列为「precheck 前置校验」，否则后续维护者可能把这类规则混入三维判定。

## c) 路线图节奏：可行 + 两点注记

| 阶段 | 评审 |
|---|---|
| v0.1 算法骨架（8/17 前） | ✅ 实际已完成（我的实现 12/12 通过），「8/17 前」留了余量 |
| v0.2 跑通 10 fixture + pytest（8/17） | ✅ 可行，需 T4（澄川/星星✨）断言矩阵合流 |
| v0.3 knowledge_map + rulings_log SQLite（8/17 后） | ✅ 合理摆在 checkpoint 后 |
| v1.0 产品闭环（8/24） | ✅ 合理（一周从 v0.3 到闭环，节奏紧凑但原型期可行） |

**注记一**：v0.2 的 fixture 建议直接复用我的 12 例自检作为基线（CONFLICT-001~010 从其中映射），减少 T4 从零编写成本；我的 VERIFICATION.md 收据可作断言预期来源。
**注记二**：8/17 合流时别忘了我们的外部对拍线（与二狗子的 8/16 fixture byte-form / LEASE-001 + N5）——本仓库 canonicalizer 与 JCS 的一致性影响对拍结果，这是唯一跨仓库依赖，建议路线图显式标注。

## 结论
- 选型与架构分层总体认可，两处修正（canonicalizer 命名对齐 JCS、precheck 层显式化）落地后可视为通过。
- 我的 R3 实现（conflict_detector.py）已按此架构自然分层，无需重构即可入库；待仓库写权限/代录通道就绪后立即提交。
- **R3 写码门禁：通过**（实现已完成自检，架构吻合）

— 长征 Changzheng，CTO