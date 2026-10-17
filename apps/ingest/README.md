# 一句话入口 CLI（M2 切片 1）

> 产品目标（`docs/product.md` M2）：人类**说一句话**（丢一段资料/一个链接）→ agent 自动入库、条目化、报冲突，有 CLI/skill 封装。
> 本目录只做 M2 的第一跳：**一句话 → 归并到 claim → 入库 → 报冲突**。不做 LLM、不做链接抓取。

## 为什么先做这一跳

知识的价值不在「存进去」，在「同一件事有两种说法时被看见」。所以入库前必须先回答：
**这两句话说的是同一个断言吗？** 说不同断言的句子塞进同一 claim，冲突检测会天天误报；
说同一件事的句子进不了同一 claim，真正的矛盾永远看不见。

`claim_norm.py` 的 `anchor = subject::predicate` 就是这条判据，且它是**确定性、离线可复算**的——
同一句话无论入库几次，anchor 都一样。这是「可验证入库」的底座，不能用 LLM 替代（同句两次跑出不同 anchor = 知识库不可审计）。

## 用法

```bash
# 先起 knowledge-map（冲突检测在它里面）
cd apps/knowledge-map && .venv/bin/python -m uvicorn main:app --port 8000

# 说两句话（同主题同谓词 → 同一 claim → 冲突被检出）
python3 apps/ingest/ingest.py "项目A的截止日期是9月19日" "项目A的截止日期改成10月3日"

# 从 stdin 每行一句
echo "项目B的价格是30元" | python3 apps/ingest/ingest.py --stdin

# 只看归并计划，不联网（评审/fixture 生成用）
python3 apps/ingest/ingest.py --dry-run "项目A的截止日期是9月19日"

# 机器可读
python3 apps/ingest/ingest.py --json "项目A的截止日期是9月19日"
```

## 退出码（契约）

| 码 | 含义 |
|---|---|
| 0 | 成功（含「无冲突」）|
| 2 | 没有输入 |
| 3 | 全部句子 UNPARSED，无可入库内容 |
| 4 | **入库失败**（服务不可达等）——必须非零，禁止假绿 |

## 归一化规则（封闭、可审计）

- 谓词表 `PREDICATES` 是**封闭集合**，扩表 = 改代码 + 加测试，不许运行时动态扩展。
- 触发词按**长度降序**匹配（「截止日期」不会被「日期」抢走）。
- 值归一化只做确定性变换：`9月19日 → --09-19`（无年份）、`2026年10月3日 → 2026-10-03`、`30元 → 30.00CNY`、`1.5万 → 15000.00CNY`。
- 相对时间**不猜具体日期**：`明天 → REL:+1d`，由上层带参照时刻解析。
- **主题缺失 → UNPARSED**，不猜主题（猜错会把不同主题的断言并成一个 claim，比不并更糟）。
- 原文（`value_raw`）与规范值（`value_norm`）都保留：判冲突看 norm，人读看 raw。

## 验收（可复现）

```bash
cd apps/ingest && python3 -m pytest tests -q
# 19 passed

# 端到端（需 knowledge-map 在跑）：
python3 ingest.py --server http://127.0.0.1:8000 "项目A的截止日期是9月19日" "项目A的截止日期改成10月3日"
# 已入库 2 条，1 个 claim：c-… (2 条)
# 发现 1 处冲突：
#   [c-…] CONFLICTED
#     {'field': 'content', 'revision': 'rev-2', 'value_a': '9月19日', 'value_b': '10月3日'}
```

## 已知缺口（下一片）

1. **值不参与判冲突的字段选择**：knowledge-map 的 `detect()` 现在按 `content` 判，同一个 claim 下多个 entry 天然 CONFLICTED。本 CLI 先把「同 claim 归并」做对，下一步要把 `value_norm` 作为独立字段入库，让「9月19日 vs 10月3日」判为 `value` 字段冲突、「同一日期不同措辞」判为非冲突。
2. **链接/长文入口**：M2 原文要求「丢一段资料/一个链接」。切片 1 只做句子；切片 2 接 `--url` 与文件输入，抓取后用同一套 `claim_norm` 逐句入库。
3. **skill 封装**：切片 3 包成 skill（`ingest`），让人在对话里直接说，不用记 CLI 参数。
