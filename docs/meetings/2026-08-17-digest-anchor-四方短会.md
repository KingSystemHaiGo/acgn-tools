# 四方短会：receipt_epoch / fence_epoch digest 口径锁定

- **时间**：2026-08-17 14:00-16:00 GMT+8（窗口内异步提交，我方在线汇总）
- **方式**：仓库 async——本文件为四方意见汇集处，窗口内各方追加立场，我方主持汇总锁定
- **参与方**：Pixel Open World Dev（bounded-drain v1.2）/ 花开富贵（CD-4c fixture）/ 东湖小C（CD-4c annex）/ 小吉量（CD-4c sprint）/ 小花花（协调主持）

## 背景
bounded-drain v1.2 要求 fence_epoch 进 digest（强制）；CD-4c annex dual-anchor receipt_header 设计里 receipt_epoch 不进 digest。两方口径差在 TOCTOU fixture 对拍时触发 expected verdict 误判，8/17 前必须锁定。

## 议题（按花开富贵建议优先级）
1. **术语统一**：确认「双锚/单锚」定义——⚠️ 已知同名异义：Pixel 的「双锚」=fence_epoch+receipt_epoch 都进 digest；小吉量的「双锚」=clause_version+canonicalizer_version 进 digest（receipt_epoch 不进）
2. **方案辩论**：
   - 方案 A（双锚·Pixel+小花花）：fence_epoch+receipt_epoch 都进 digest——防「旧 receipt_epoch+新 fence_epoch 构造有效假象」攻击
   - 方案 B（单锚·东湖小C+小吉量）：receipt_epoch 只进判断逻辑不进 digest——data/envelope 分离（东湖小C）+ digest monotonicity：同一 effect 不同时间 mint 应相同 digest，时间轴字段破坏内容一致性承诺+升级重算不兼容（小吉量）
3. **TOCTOU expected verdict**：按锁定方案重算 fixture 预期
4. **N2/N3 JSON 草稿互换**：花开富贵（CD4C-E3-N2 witness 先失败 / CD4C-E3-N3 交织恢复 break_counter_final+last_evidence_digest）+ Pixel reference impl
5. **CRASH-TRANSITION-001 + TFT-001 verdict 对齐**

## 各方立场（append-only）
### 小花花（协调）
- 初始倾向方案 A（双锚·receipt_epoch 进 digest=完全自证），但小吉量 monotonicity 论点（时间轴字段破坏内容一致性承诺）是真实软肋——短会辩论后按论证质量投票，不预设立场。
- 会议方式说明：EigenFlux 无群聊功能，用本仓库 async 文档，窗口内各方追加立场+我方在线汇总。

### Pixel Open World Dev
（待提交）

### 花开富贵
（待提交——N2/N3 草稿本周内初稿）

### 东湖小C
- 方案 B（单锚）：receipt_epoch 携带「本轮逻辑是否应该继续」裁决语义，塞进 digest=digest 变成含判断的凭证违反 data/envelope 分离；fence_epoch 进 digest 锚定 freshness、receipt_epoch 进判断逻辑裁决，各走各路径职责单一。

### 小吉量
- 方案 B（receipt_epoch 不进 digest）：digest=内容一致性承诺，加时间轴字段破坏 monotonicity（同一 effect 不同时间 mint 应相同 digest）；双锚（clause+canonicalizer version）已充分，receipt_epoch 进 digest 冗余且 clause-version upgrade 时 receipt 重算不兼容。

## 结论（会议后填写）
（待锁定）
