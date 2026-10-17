#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim_norm 单元测试——M2 切片 1 的验收断言（归一化必须确定、可复算、不猜）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claim_norm import group, norm_value, parse  # noqa: E402


def test_parse_deadline_cn_date():
    c = parse("项目 A 的截止日期是 9 月 19 日")
    assert c.status == "OK"
    assert c.predicate == "deadline"
    assert c.subject == "项目A"
    assert c.value_norm == "--09-19"


def test_parse_deadline_with_year():
    c = parse("项目A截止日期为2026年10月3日")
    assert c.status == "OK"
    assert c.value_norm == "2026-10-03"


def test_longest_trigger_wins():
    """"截止日期"必须整体吃掉，不能被更短的"日期"抢走导致主题残留。"""
    c = parse("项目A的截止日期是9月19日")
    assert c.predicate == "deadline"
    assert c.subject == "项目A"


def test_parse_price_normalizes_yuan():
    c = parse("项目B的价格是30元")
    assert c.status == "OK"
    assert c.predicate == "price"
    assert c.value_norm == "30.00CNY"


def test_owner_without_subject_is_unparsed():
    """只有谓词没有主题 → 必须 UNPARSED（不许猜主题，否则不同主题的断言会被错并成一个 claim）。"""
    c = parse("负责人是张三")
    assert c.status == "UNPARSED"
    assert c.predicate == "owner"
    assert c.reason == "主题为空"


def test_owner_with_subject_normalizes():
    c = parse("项目A的负责人是张三")
    assert c.status == "OK"
    assert c.subject == "项目A"
    assert c.value_norm == "张三"


def test_unparsed_when_no_predicate():
    c = parse("今天天气不错")
    assert c.status == "UNPARSED"
    assert c.anchor == ""


def test_empty_sentence():
    assert parse("   ").status == "EMPTY"


def test_same_anchor_groups_conflicting_assertions():
    """产品核心：同一主题+同一谓词的两句话必须落进同一 claim，否则冲突检测永远看不见。"""
    g = group(["项目A的截止日期是9月19日", "项目A的截止日期改成10月3日"])
    assert list(g.keys()) == ["项目A::deadline"]
    assert len(g["项目A::deadline"]) == 2


def test_different_subject_not_merged():
    g = group(["项目A的截止日期是9月19日", "项目B的截止日期是9月19日"])
    assert len([k for k in g if k]) == 2


def test_norm_value_is_deterministic():
    sentence = "项目A的截止日期是9月19日"
    assert parse(sentence) == parse(sentence)


def test_relative_date_marked_not_invented():
    """"明天"不许猜成具体日期——只标相对量，由上层带参照时刻解析。"""
    c = parse("项目A的截止日期是明天")
    assert c.value_norm == "REL:+1d"


def test_money_wan_and_k():
    assert norm_value("price", "1.5万") == "15000.00CNY"
    assert norm_value("price", "800k") == "800000.00CNY"
