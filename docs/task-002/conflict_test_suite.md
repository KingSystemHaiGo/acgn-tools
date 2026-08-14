# T002-R4：conflict_test_suite.md（可执行断言套件 v0.1）

作者：澄川（测试断言，T002-R4）｜交付：2026-08-14｜状态：草稿（待星星 fixture 全文+长征 R3 实现后对拍）｜依据：T002-R2 算法规格+T4 质量矩阵 v0.1
协作：星星 ✨（矩阵/覆盖）｜断言纪律：digest 命中≠语义通过，必须走三维规则裁决后断言状态

## 0. 断言模板（每条用例按此结构）

```python
def assert_case(case):
    assert result.status == case.expected_status  # SUPERSEDED/CONFLICTED/REJECTED
    if case.expected_status == "CONFLICTED":
        assert result.evidence is not None
        for triple in result.evidence:
            assert len(triple) == 3  # [字段名, 触发修订号, 双方值]
            assert triple[0] in case.conflict_fields
    assert input_count == success + local_skip + hard_fail
    assert len({e.entry_id for e in inputs}) == len(inputs)  # item_id 唯一
```

## 1. 用例断言（对应 T4 矩阵 §2 十条）

### 正例组（F1×V1 + F2×V1）——必 PASS

- CONFLICT-001（华为收入互斥→conflicted）：status==CONFLICTED；evidence 三元组含 [field, rev, valA, valB]
- CONFLICT-002（X 安全 vs 危险 validity 重叠→conflicted）：status==CONFLICTED；validity 字段进 evidence

### 负例组（F1×V2）——必 FAIL 不误判

- CONFLICT-003（derived 细化→superseded）：status==SUPERSEDED；断言 NOT CONFLICTED
- CONFLICT-004（血糖条件不重叠→superseded）：status==SUPERSEDED；validity 不重叠断言

### 边界组（F3×V2 + F3×V3）

- CONFLICT-005（独立 source 措辞相似→升格 conflicted 人工仲裁）：status==CONFLICTED；不自动 resolve
- CONFLICT-006（validity 重叠语义不明→conflicted 建议对照原文）：status==CONFLICTED；输出带建议对照标记

### 负控/不可逆组（F4×V3 + F5×V3）——必 REJECTED

- CONFLICT-007（循环依赖）：status in (CONFLICTED, REJECTED)，循环依赖判出即止
- CONFLICT-008（fence 封口收 derived）：status==REJECTED
- CONFLICT-009（conflicted 收 derived）：status==REJECTED；只能用户仲裁
- CONFLICT-010（derived 无 parent）：构造失败→REJECTED

## 2. 断言覆盖（V5：T1 每规则 ≥1 用例）

见 T4 质量矩阵 §4 覆盖表（11 行全覆盖，本套件每条断言对应矩阵格）。

## 3. 验收

- 每条用例有必 PASS/必 FAIL/必 REJECTED 断言 ✅
- 覆盖「conflicted 不自动 resolve」✅（005/006/009）
- evidence 三元组断言 ✅（conflicted 必带）
- 收据守恒断言 ✅
- 待：星星 fixture 全文对齐 + 长征 R3 实现后跑通回传字节级收据
