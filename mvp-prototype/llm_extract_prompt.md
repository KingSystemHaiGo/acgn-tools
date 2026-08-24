# LLM 抽取 Prompt 设计 + 课标结构化输入 Schema（生产路径规格）

> 对应 `extractor.py` 中 `extract_with_llm` 的待实现生产路径。
> 原型当前用 heuristic fallback；生产应接 LLM。本文件是 prompt + 输入格式的规格说明（研究/设计交付）。

---

## 1. 输入：课标/教材结构化片段

建议输入为带层级的结构化文本（非纯段落），便于解析器锚定：

```
[领域] 数与代数
  [学段] 小学
    [主题] 小数的意义
      [知识点] 小数与整数的位值关系
      [知识点] 小数加减法（需先掌握：整数加减法、通分）
```

解析器（`curriculum_parser`，待实现）把上述转为 seed 节点 + 已知前置关系，作为 LLM 抽取的上下文锚点，降低幻觉。锚定 2022 课标不绑教材版本。

---

## 2. LLM 抽取 Prompt（模板）

```
你是一名教育知识图谱构建助手。给定课标/教材结构化片段，抽取"微知识点"候选与"依赖边"。
约束：
1. 只输出 JSON，不输出解释。
2. 依赖边(relation=prerequisite)表示"target 的学习必须先掌握 source"。
3. 不复制教材原文；只给知识点短标签(<=24字)与课标锚点引用。
4. 每个对象必须带 source_ref（课标条目/教材锚点，不存原文）。
输出 schema：
{
  "nodes":[{"id":"kp-xxx","label":"...","grade":"小学","std_anchor":"2022课标-数与代数-..."}],
  "edges":[{"source":"kp-xxx","target":"kp-yyy","relation":"prerequisite","evidence":"..."}]
}
输入片段：
<<INPUT>>
```

模型返回后，`extract_with_llm` 包装 `Provenance(extraction_method="llm", extraction_model=<model>)` 并交 `review_gate` 人审。

---

## 3. 与 consume-gate 衔接

LLM 输出 = 候选；全部走 `apply_review` 人审，approved 才入库。LLM 不决定最终依赖边（教育正确性归人审）。

---

## 4. 防幻觉要点

- 用 `curriculum_parser` 的已知前置关系约束 LLM，避免凭空造边。
- 输出 schema 强制 `source_ref`，缺失则视为无效候选。
- 一致性校验（`verification.py`）兜底：环检测 + 悬空边 + 溯源完整。
