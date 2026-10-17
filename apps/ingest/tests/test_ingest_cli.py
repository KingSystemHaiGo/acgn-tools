#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingest CLI 验收测试：dry-run 归并计划 + 网络失败必须显式非零退出（不许假绿）。"""

import json
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "ingest.py"


def run(args, stdin: str | None = None):
    return subprocess.run(
        [sys.executable, str(APP), *args],
        capture_output=True, text=True, input=stdin, timeout=30,
    )


def test_dry_run_groups_same_anchor():
    r = run(["--dry-run", "项目A的截止日期是9月19日", "项目A的截止日期改成10月3日"])
    assert r.returncode == 0, r.stderr
    assert "项目A::deadline" in r.stdout
    assert "--09-19" in r.stdout
    assert "--10-03" in r.stdout


def test_dry_run_json_shape():
    r = run(["--dry-run", "--json", "项目A的截止日期是9月19日"])
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert "项目A::deadline" in payload
    assert payload["项目A::deadline"][0]["value_raw"] == "9月19日"


def test_stdin_mode():
    r = run(["--dry-run", "--stdin"], stdin="项目A的截止日期是9月19日\n项目B的价格是30元\n")
    assert r.returncode == 0, r.stderr
    assert "项目A::deadline" in r.stdout
    assert "项目B::price" in r.stdout


def test_no_input_exits_2():
    r = run([])
    assert r.returncode == 2


def test_all_unparsed_exits_3():
    r = run(["今天天气不错"], )
    assert r.returncode == 3


def test_unreachable_server_is_loud():
    """入库失败必须非零退出——「假装成功」比失败更贵。"""
    r = run(["--server", "http://127.0.0.1:9", "项目A的截止日期是9月19日"])
    assert r.returncode == 4, (r.returncode, r.stdout, r.stderr)
    assert "入库失败" in r.stderr
