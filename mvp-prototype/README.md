# MVP 教育语义自动建图 Agent（原型骨架）

RESEARCH-001 v1.0 终稿第 6 节"MVP 范围建议"的技术预研骨架。
本目录是**原型/预研**，用于验证架构可行性，非生产构建。

## 架构
课标/教材文本 → [抽取] → 候选节点+依赖边 → [consume-gate 人审] → 已发布开放图谱(JSON-LD+CSV)

## 组件
- `kg_schema.py` 数据模型 + 溯源链(Provenance)
- `extractor.py` 候选抽取（LLM 占位 + 离线 heuristic fallback）
- `review_gate.py` consume-gate 人审协议（依赖边必须人审）
- `export_openkg.py` 开放图谱导出（JSON-LD + CSV + 字节级收据）
- `run_demo.py` 端到端离线演示

## 运行
```bash
python3 run_demo.py
```
输出在 `output/`：knowledge-graph.jsonld、nodes.csv、edges.csv、receipt.json。

## 设计约束（来自 RESEARCH-001）
- 依赖边 = consume-gate 语义：未人审(pending)不入库。
- 每个节点/边带溯源 evidence 链；溯源链完整率目标 100%。
- 只存知识点+依赖边+课标锚点，不存教材原文（版权）。
- 锚定 2022 课标不绑教材版本。

## 与 cn-primary-math-knowledge-graph 对齐
该仓库（MIT）现有 95 节点 / 111 边 / 19 课标锚点。
本原型输出的 JSON-LD / CSV 字段（id, label, grade, std_anchor, provenance）
可映射为该仓库节点/边格式，作为自动建图增量来源。
