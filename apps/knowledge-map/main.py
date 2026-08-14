"""
knowledge-map 后端 —— 花火工作室 MVP v0.1
个人知识宇宙：导入资料 → 知识条目 → 冲突检测 → 用户仲裁（三态摊开）→ 年轮追加 → 回看知识地图

技术栈：FastAPI + SQLite + conflict_detector（T002-R3）
运行：uvicorn main:app --reload --port 8000
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---- 复用 T002 conflict_detector（若可用）----
DETECTOR_PATH = Path(__file__).parent.parent / "conflict-detector" / "conflict_detector.py"
try:
    import sys
    sys.path.insert(0, str(DETECTOR_PATH.parent))
    from conflict_detector import detect  # type: ignore
    HAS_DETECTOR = True
except Exception:
    HAS_DETECTOR = False

DB_PATH = Path(__file__).parent / "knowledge.db"

app = FastAPI(title="花火工作室 · 个人知识宇宙 MVP", version="0.1")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ---------- 数据层 ----------
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                claim_id TEXT, entry_id TEXT PRIMARY KEY, revision TEXT,
                effect_digest TEXT, lineage_link TEXT, parent_claim_id TEXT,
                established INTEGER, fence INTEGER, source_role TEXT,
                content TEXT, provenance TEXT, created_at TEXT,
                tri_state TEXT DEFAULT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS rulings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT, choice TEXT, note TEXT, created_at TEXT
            )
        """)
        # 兼容旧库：已有 entries 表无 tri_state 列则补上
        cols = [r[1] for r in c.execute("PRAGMA table_info(entries)")]
        if "tri_state" not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN tri_state TEXT DEFAULT NULL")


init_db()


def canonical(text: str) -> str:
    """effect_digest：canonicalizer 简化版（JCS 风格：UTF-8 规范化 + SHA-256）"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------- API 模型 ----------
class ImportReq(BaseModel):
    text: str
    title: Optional[str] = None


class ArbitrateReq(BaseModel):
    claim_id: str
    choice: str  # KEEP_A / KEEP_B / SPLIT / REDEFINE
    note: Optional[str] = ""


class MarkReq(BaseModel):
    entry_id: str
    state: str  # nascent / shelved / seeking（三态手动标记）
    note: Optional[str] = ""


# ---------- API ----------
@app.post("/api/import")
def import_text(req: ImportReq):
    """导入一段资料 → 拆成知识条目（按行/句切分）
    同一批导入 = 同一 claim（主题）下的多个 entry——多行断言互相矛盾时即可检出冲突。
    claim_id 基于标题（或首行摘要），entry 按行展开。
    """
    if not req.text.strip():
        raise HTTPException(400, "内容为空")
    now = datetime.now().isoformat(timespec="seconds")
    lines = [ln.strip() for ln in req.text.splitlines() if ln.strip()]
    if not lines:
        lines = [req.text.strip()]

    # claim 锚点：标题优先，否则用首行（同批导入共享 claim_id）
    anchor = (req.title or lines[0]).strip()
    claim_id = "c-" + canonical(anchor)[:16]

    created = []
    with db() as c:
        # 同 claim 已有条目则作为前驱（后续 entry 为派生候选）
        existing = c.execute(
            "SELECT entry_id FROM entries WHERE claim_id=? ORDER BY established DESC LIMIT 1",
            (claim_id,),
        ).fetchone()
        parent = existing["entry_id"] if existing else None
        for i, line in enumerate(lines):
            entry_id = f"{claim_id}-e{i}-{canonical(line)[:6]}"
            digest = canonical(line)
            lineage = "derived" if parent else "source"
            c.execute(
                """INSERT OR IGNORE INTO entries
                   (claim_id, entry_id, revision, effect_digest, lineage_link,
                    parent_claim_id, established, fence, source_role, content, provenance, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (claim_id, entry_id, f"rev-{i + 1}", digest, lineage,
                 parent, 0, None, "source", line, req.title or "", now),
            )
            created.append({"claim_id": claim_id, "entry_id": entry_id, "content": line[:40]})
    return {"imported": len(created), "claim_id": claim_id, "entries": created, "detector": HAS_DETECTOR}


@app.get("/api/conflicts")
def list_conflicts():
    """冲突检测：同 claim 多 entry → 三维判定 → conflicted 列表"""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM entries WHERE claim_id IN (SELECT claim_id FROM entries GROUP BY claim_id HAVING COUNT(*)>1)"
        ).fetchall()

    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["claim_id"], []).append(dict(r))

    conflicts = []
    for claim_id, entries in groups.items():
        if not HAS_DETECTOR:
            # 无检测器时：同 claim 多 entry 且 digest 不同即标 conflicted（简化）
            digests = {e["effect_digest"] for e in entries}
            verdict = "CONFLICTED" if len(digests) > 1 else "OK"
        else:
            try:
                result = detect(entries)
                verdict = result.verdict if hasattr(result, "verdict") else result.get("verdict", "OK")
            except Exception:
                verdict = "CONFLICTED"
        if verdict == "CONFLICTED":
            conflicts.append({
                "claim_id": claim_id,
                "entries": entries,
                "verdict": verdict,
                "evidence": [{"field": "content", "values": [e["content"][:50] for e in entries]}],
            })
    return {"conflicts": conflicts, "count": len(conflicts)}


@app.post("/api/arbitrate")
def arbitrate(req: ArbitrateReq):
    """用户仲裁四选一：KEEP_A / KEEP_B / SPLIT / REDEFINE → 年轮追加（append-only）"""
    choice = req.choice.upper()
    if choice not in ("KEEP_A", "KEEP_B", "SPLIT", "REDEFINE"):
        raise HTTPException(400, "choice 必须是 KEEP_A/KEEP_B/SPLIT/REDEFINE")
    now = datetime.now().isoformat(timespec="seconds")
    with db() as c:
        c.execute(
            "INSERT INTO rulings (claim_id, choice, note, created_at) VALUES (?,?,?,?)",
            (req.claim_id, choice, req.note, now),
        )
    return {"ok": True, "claim_id": req.claim_id, "choice": choice, "created_at": now}


@app.post("/api/mark")
def mark(req: MarkReq):
    """三态手动标记：nascent（纳入）/ shelved（搁置）/ seeking（求索）
    知识宇宙最小闭环：用户对条目手动定三态，覆盖自动推断。"""
    state = req.state.lower()
    if state not in ("nascent", "shelved", "seeking"):
        raise HTTPException(400, "state 必须是 nascent/shelved/seeking")
    now = datetime.now().isoformat(timespec="seconds")
    with db() as c:
        row = c.execute(
            "SELECT entry_id FROM entries WHERE entry_id=?", (req.entry_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, f"entry {req.entry_id} 不存在")
        c.execute(
            "UPDATE entries SET tri_state=? WHERE entry_id=?", (state, req.entry_id)
        )
        # 标记动作也进年轮（append-only 审计）
        c.execute(
            "INSERT INTO rulings (claim_id, choice, note, created_at) VALUES (?,?,?,?)",
            ("mark:" + req.entry_id[:20], "MARK_" + state.upper(), req.note, now),
        )
    return {"ok": True, "entry_id": req.entry_id, "state": state, "created_at": now}


@app.get("/api/knowledge-map")
def knowledge_map():
    """知识宇宙：三态分布（纳入/搁置/求索）+ 全量条目列表（含手动标记 tri_state）"""
    with db() as c:
        total = c.execute("SELECT COUNT(*) n FROM entries").fetchone()["n"]
        entries = c.execute(
            "SELECT claim_id, entry_id, content, source_role, tri_state, created_at FROM entries ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    # 三态：手动标记 tri_state 优先，未标记则按 source_role 推断
    by_role = {"nascent": 0, "shelved": 0, "seeking": 0}
    for e in entries:
        state = e["tri_state"]
        if not state:
            if e["source_role"] in ("source", "confirmed"):
                state = "nascent"
            elif e["source_role"] in ("superseded", "derived"):
                state = "shelved"
            elif e["source_role"] == "conflicted":
                state = "seeking"
            else:
                state = "nascent"
        by_role[state] = by_role.get(state, 0) + 1
    out = []
    for r in entries:
        d = dict(r)
        d["tri_state"] = d.get("tri_state") or None
        out.append(d)
    return {
        "total": total,
        "by_role": by_role,
        "entries": out,
    }


@app.get("/api/rulings")
def rulings():
    """年轮记录（append-only 时间线）"""
    with db() as c:
        rows = c.execute(
            "SELECT claim_id, choice, note, created_at FROM rulings ORDER BY id"
        ).fetchall()
    return {"rulings": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/health")
def health():
    return {"status": "ok", "detector": HAS_DETECTOR, "time": datetime.now().isoformat()}


# 前端静态文件
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
