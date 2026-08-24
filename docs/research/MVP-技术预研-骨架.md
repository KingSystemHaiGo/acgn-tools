# MVP 教育语义自动建图 Agent —— 技术预研骨架

> 配套：RESEARCH-001 v1.0 终稿（第 6 节 MVP 范围建议）
> 性质：技术预研 / 原型骨架，用于验证架构可行性，供决策参考；非生产构建。
> 日期：2026-08-20
> 代码：`mvp-prototype/`（已离线跑通端到端）

---

## 1. 定位与边界

- 目标：把"开放 + 锚定课标 + 可追溯微知识点图谱 + 教育语义自动建图 agent"从文档结论变成可运行骨架。
- 本骨架已离线跑通端到端（见 `mvp-prototype/run_demo.py`），证明"抽取 → consume-gate 人审 → 溯源导出"链路成立。
- **不做**：通用竞品调研（CatKing 领地）；通用建图基建（引用 GraphRAG/Graphiti）；C 端产品（与工作室 B2B 定位一致）。
- **不做**：完整小学数学全册抽取（留给 MVP 正式构建，需小花花确认方向后启动）。

---

## 2. 架构

```
课标/教材文本 (用户授权)
        │
        ▼
[抽取层 extractor]
   - LLM 抽取（生产路径，extract_with_llm 占位）
   - heuristic fallback（原型演示，离线可跑）
   → 候选 KnowledgeNode + 候选 DependencyEdge(prerequisite)
        │
        ▼
[consume-gate 人审层 review_gate]
   - 依赖边必须人审：pending 不入库
   - 决策：approve / reject / edit
   - 写入 reviewer + review_at + review_status
        │
        ▼
[导出层 export_openkg]
   - JSON-LD（开放图谱，schema.org 风格 vocab）
   - nodes.csv / edges.csv（仅 approved 边）
   - receipt.json（字节级 sha256，溯源可审计）
        │
        ▼
已发布开放图谱 (MIT) —— 增量合并进 cn-primary-math-knowledge-graph
```

---

## 3. 数据模型（溯源链是核心）

每个节点/边携带 `Provenance`：

| 字段 | 含义 | 约束 |
|---|---|---|
| source_ref | 课标条目/教材锚点（不存原文） | 非空 |
| extraction_method | llm / heuristic-fallback | 非空 |
| extraction_model | 模型名 或 heuristic-v1 | 非空 |
| extracted_at | 抽取时间戳(UTC) | 非空 |
| reviewer | 人审者 | approved 边必填 |
| review_status | pending/approved/rejected/edited | 非空 |
| review_at | 人审时间戳 | approved 必填 |
| evidence | 溯源引用（锚点描述，非原文复制） | 建议非空 |

**溯源链完整率** = 带完整 provenance 的节点/边数 / 总数。目标 **100%**。

---

## 4. consume-gate 人审协议

- 依赖边 = consume-gate 语义（引用 CatKing approval gates / effect receipts 研究域）。
- 候选边默认不入库；只有 `apply_review` 标记为 `approved` 才进入 published graph。
- `rejected` / `edited` / `pending` 边保留在候选集，不写入开放图谱。
- 这保证"教育正确性"——依赖边必须人确认，机器只提候选。

---

## 5. 与 cn-primary-math-knowledge-graph 对齐

- 该仓库（MIT）现有 95 节点 / 111 边 / 19 课标锚点，是开源先发占位。
- 本原型输出字段（`id, label, grade, std_anchor, provenance`）可直接映射为仓库节点/边格式。
- 自动建图产出作为"增量来源"：新抽取的候选经人审后合并进主库，主库保持人工策展质量。
- 版权：图谱只存知识点+依赖边+课标锚点，教材原文不存；版本差异走独立映射层（锚定 2022 课标不绑版本）。

---

## 6. MVP 验收口径（量化，细化 v1.0 第 6 节）

| 指标 | 目标 | 测量方式 |
|---|---|---|
| 单册知识点覆盖率 | ≥90% | 抽取节点数 / 课标列出的知识点数 |
| 依赖边人审通过率 | ≥85% | approved 边 / 候选边 |
| 溯源链完整率 | 100% | 带完整 provenance 的入库对象占比 |
| 课标锚定率 | 100% | 节点带 std_anchor 比例（锚定 2022 课标） |

---

## 7. 文件结构

```
mvp-prototype/
  kg_schema.py        数据模型 + Provenance 溯源
  extractor.py        抽取（LLM 占位 + heuristic fallback）
  review_gate.py      consume-gate 人审
  export_openkg.py    开放图谱导出（JSON-LD+CSV+收据）
  run_demo.py         端到端离线演示
  README.md           说明
  output/             演示产物（jsonld/csv/receipt）
```

---

## 8. 已知限制与下一步

- **限制1**：当前 heuristic 抽取是规则占位，质量远低于 LLM；生产必须接 LLM（`extract_with_llm` 已留接口）。
- **限制2**：样例仅 5 句；未覆盖全册、跨册依赖、循环依赖检测。
- **限制3**：人审目前是批量 approve；生产需交互式逐条确认 + 冲突检测（复用工作室冲突检测能力）。
- **下一步**（需小花花确认 MVP 启动后）：
  1. 接 LLM 抽取 + 课标结构化输入解析
  2. 人审 UI / 批量导入接口
  3. 循环依赖检测 + 一致性校验
  4. 增量合并进 cn-primary-math-knowledge-graph 的 CI 流程

---

## 9. 已补充：一致性校验 + LLM 抽取规格（2026-08-22）

- `verification.py`：循环依赖检测（DFS 三色）+ 引用完整性 + 溯源/锚定合规校验。
  - 演示（`run_verify_demo.py`）：正常图谱 passed=True、无环、溯源率 1.0；注入 `kp-006->kp-001` 循环后被检出（环 kp-005->kp-006->kp-001->...->kp-005）。
  - 已知：heuristic fallback 不填 `std_anchor`，故演示锚定率 0.0；生产经 `curriculum_parser` + LLM 抽取填充，方可达标（MVP 验收口径要求 100%）。
- `llm_extract_prompt.md`：LLM 抽取生产路径规格——课标结构化输入 schema + 抽取 prompt 模板 + consume-gate 衔接 + 防幻觉要点。已落地：`curriculum_parser.py`（课标结构化解析，seed 节点带 std_anchor，锚定率可达 100%）+ `extractor.extract_with_llm` 改为真实 OpenAI 兼容 /chat/completions 调用（缺密钥清晰报错不静默）。演示见 `run_curriculum_demo.py`（锚定率 1.0）。
- `review_cli.py`：consume-gate 人审 CLI（`--auto-approve` / `--decisions` / `--interactive` 三模式），把候选边经人审入库并跑校验。覆盖设计文档"下一步"第 2 项（人审批量/交互入口）。

---

> 这是预研骨架，已在本地跑通（抽取 + consume-gate 人审 + 溯源导出 + 一致性校验）。等小花花确认方向 + MVP 范围后，可据此直接升为正式构建。
