#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claim_norm.py — 一句话入口的断言归一化（M2 切片 1）
=================================================
产品目标（docs/product.md M2）：人类**说一句话**（丢一段资料/一个链接）→ agent 自动入库、条目化、报冲突。

本模块只做第一跳：把中文口语句子归一到 (subject, predicate, value, anchor, canonical_text)。
- anchor = subject::predicate —— 同一主题+同一谓词的多条断言必须落进**同一 claim**，
  冲突检测才有东西可比（不同 claim 永远不冲突）。
- 归一化是**显式且可审计**的：只做字符串级确定性变换，不做语义猜测；
  认不出的句子标 UNPARSED 而不是猜一个 predicate（宁可漏归并，不可错归并）。

设计纪律：
1. 不做 LLM 调用——这一跳必须离线可复算，否则同一句话两次入库会得到不同 anchor。
2. 谓词表是封闭集合，扩表 = 显式改代码 + 加测试，不许运行时动态扩展。
3. 值归一化保留原文（raw）与规范值（norm）两份，判冲突用 norm，展示用 raw。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ── 封闭谓词表：key = 规范谓词名，value = 触发词（按长度降序匹配，避免「日期」吃掉「截止日期」）──
PREDICATES: dict[str, tuple[str, ...]] = {
    "deadline": ("截止日期", "截止时间", "deadline", "截稿"),
    "price": ("价格", "报价", "费用", "单价", "多少钱"),
    "owner": ("负责人", "owner", "对接人", "责任人"),
    "status": ("状态", "进度"),
    "version": ("版本", "version", "版本号"),
    "location": ("地点", "位置", "地址"),
    "quantity": ("数量", "件数", "人数"),
}

_TRIGGERS = sorted(
    ((trigger, pred) for pred, triggers in PREDICATES.items() for trigger in triggers),
    key=lambda pair: len(pair[0]),
    reverse=True,
)

# 断言连接词：把「主题」和「值」分开（是/为/:/＝/改成/改为/改到）
_SEP = re.compile(r"(?:改成|改为|改到|调整为|定为|设为|变成|是|为|[:：=＝])")

_CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

_DATE_CN = re.compile(r"(?:(\d{4})年)?(\d{1,2})月(\d{1,2})[日号]")
_DATE_ISO = re.compile(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})")
_MONEY = re.compile(r"(\d+(?:\.\d+)?)\s*(元|块|w|万|k|千)?", re.IGNORECASE)


def _clean(text: str) -> str:
    """去空白/首尾标点——只做确定性的字符级清洗，不改语义。"""
    return re.sub(r"[\s　]+", "", text).strip("，,。.；;！!？?“”\"'（）()")


def _norm_cn_int(token: str) -> Optional[int]:
    if token.isdigit():
        return int(token)
    if token in _CN_NUM:
        return _CN_NUM[token]
    if len(token) == 2 and token[0] == "十" and token[1] in _CN_NUM:
        return 10 + _CN_NUM[token[1]]
    if len(token) == 2 and token[1] == "十" and token[0] in _CN_NUM:
        return _CN_NUM[token[0]] * 10
    return None


def norm_value(predicate: str, value: str) -> str:
    """按谓词做值归一化；认不出的形态原样返回（标记由调用方决定，不在这里猜）。"""
    v = _clean(value)
    if predicate == "deadline":
        m = _DATE_ISO.search(v)
        if m:
            y, mo, d = (int(x) for x in m.groups())
            return f"{y:04d}-{mo:02d}-{d:02d}"
        m = _DATE_CN.search(v)
        if m:
            y = int(m.group(1)) if m.group(1) else 0  # 0 = 未指定年份，保留待补
            mo, d = int(m.group(2)), int(m.group(3))
            return f"{y:04d}-{mo:02d}-{d:02d}" if y else f"--{mo:02d}-{d:02d}"
        if "明天" in v:
            return "REL:+1d"
        if "后天" in v:
            return "REL:+2d"
        if "今天" in v:
            return "REL:+0d"
        return v
    if predicate == "price":
        m = _MONEY.fullmatch(v)
        if m:
            amount, unit = m.group(1), (m.group(2) or "").lower()
            factor = {"w": 10000, "万": 10000, "k": 1000, "千": 1000}.get(unit, 1)
            return f"{float(amount) * factor:.2f}CNY"
        return v
    if predicate == "quantity":
        m = re.fullmatch(r"([零一二三四五六七八九十]+|\d+)", v)
        if m:
            n = _norm_cn_int(m.group(1))
            if n is not None:
                return str(n)
        return v
    return v


@dataclass(frozen=True)
class Claim:
    """一句话归一化的结果。status=OK 才进 claim；UNPARSED 也留着（要展示给人看，不能静默丢）。"""

    subject: str
    predicate: str
    value_raw: str
    value_norm: str
    status: str  # OK | UNPARSED | EMPTY
    reason: str = ""

    @property
    def anchor(self) -> str:
        """subject::predicate；任一侧缺失则为空串——空 anchor 不许进 claim 分组。"""
        if not self.subject or not self.predicate:
            return ""
        return f"{self.subject}::{self.predicate}"

    def as_line(self) -> str:
        """进 import 的文本行：值带原文，方便人读；同一 claim 的多行互相矛盾即可检出冲突。"""
        return f"{self.value_raw}"


def parse(sentence: str) -> Claim:
    """一句话 → Claim。确定性、无外部依赖、可复算。"""
    raw = _clean(sentence)
    if not raw:
        return Claim("", "", "", "", "EMPTY", "空句子")

    # 1) 找谓词触发词（最长优先）
    pred = None
    hit_trigger = ""
    for trigger, p in _TRIGGERS:
        if trigger in raw:
            pred, hit_trigger = p, trigger
            break

    # 2) 按分隔符切主题 / 值
    parts = _SEP.split(raw, maxsplit=1)
    if len(parts) != 2:
        # 没有连接词：用触发词位置切（「截止日期9月19日」）
        if hit_trigger:
            idx = raw.index(hit_trigger)
            subject = raw[:idx]
            value = raw[idx + len(hit_trigger):]
            parts = [subject, value]
        else:
            return Claim("", "", "", "", "UNPARSED", "无连接词且无谓词触发词")

    left, value_raw = parts[0], parts[1]

    if pred is None:
        # 没有谓词：从主题侧剥离触发词，再把主题自身当谓词（「A 项目的负责人是张三」已由上一步吃掉触发词）
        for trigger, p in _TRIGGERS:
            if trigger in left:
                pred, hit_trigger = p, trigger
                left = left.replace(trigger, "", 1)
                break

    subject = _clean(left)
    # 触发词落在主题侧（「负责人是张三」/「项目A的截止日期是…」）→ 从主题剥离，否则主题会与谓词同名
    if hit_trigger and hit_trigger in subject:
        subject = _clean(subject.replace(hit_trigger, "", 1))
    # 「项目A的」→「项目A」：结构性后缀，剥离不改变所指
    if subject.endswith("的"):
        subject = subject[:-1].strip()
    if pred is None:
        return Claim(subject, "", value_raw, value_raw, "UNPARSED", "未识别的谓词")
    if not subject:
        return Claim("", pred, value_raw, value_raw, "UNPARSED", "主题为空")
    if not _clean(value_raw):
        return Claim(subject, pred, "", "", "UNPARSED", "值为空")

    return Claim(subject, pred, value_raw, norm_value(pred, value_raw), "OK")


def group(sentences: list[str]) -> dict[str, list[Claim]]:
    """按 anchor 分组：只有 OK 的 Claim 进组；UNPARSED 单列在 "" 键下。"""
    out: dict[str, list[Claim]] = {}
    for s in sentences:
        c = parse(s)
        out.setdefault(c.anchor if c.status == "OK" else "", []).append(c)
    return out
