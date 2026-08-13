# 知识地图 MVP v0.1（个人知识宇宙）

> 花火工作室首个可运行产品：导入资料 → 冲突检测 → 用户仲裁（你才是裁判）→ 年轮追加

## 运行
```bash
cd apps/knowledge-map
uv sync
.venv/bin/python -m uvicorn main:app --port 8000
# 浏览器打开 http://localhost:8000
```

## API
- `POST /api/import`：导入资料（同批=同一 claim 多 entry）
- `GET /api/conflicts`：冲突列表（三维判定）
- `POST /api/arbitrate`：仲裁四选一（KEEP_A/KEEP_B/SPLIT/REDEFINE）
- `GET /api/knowledge-map`：三态分布
- `GET /api/rulings`：年轮记录（append-only）

## 已验证（2026-08-13 21:36）
- ✅ 导入「华为收入>1000亿 / 华为收入≤1000亿」→ 同一 claim CONFLICTED + 证据链
- ✅ 仲裁 SPLIT → 年轮追加
- ✅ 全链路 curl 跑通

## 技术栈
FastAPI + SQLite + conflict_detector（T002-R3，detector 在线）
