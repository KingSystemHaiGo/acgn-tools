# 个人知识宇宙 MVP v0.1（花火工作室首个产品）

> **产品方向**：个人知识宇宙——你的知识被组织、被看见、被记得。
> 导入资料 → 知识条目化（三态：纳入/搁置/求索）→ 知识地图 → 冲突提醒（子功能）→ 仲裁 → 年轮沉淀。
> ⚠️ 冲突检测只是宇宙里「发现知识打架」的一个能力，不是产品本身。

## 运行
```bash
cd apps/knowledge-map
uv sync
.venv/bin/python -m uvicorn main:app --port 8000
# 浏览器打开 http://localhost:8000
```

## API
- `POST /api/import`：导入知识（同批=同一 claim 多 entry）
- `GET /api/knowledge-map`：**知识宇宙核心**——三态分布（纳入/搁置/求索）+ 全量条目
- `GET /api/conflicts`：冲突提醒（子功能，三维判定）
- `POST /api/arbitrate`：仲裁四选一（KEEP_A/KEEP_B/SPLIT/REDEFINE）
- `GET /api/rulings`：年轮记录（append-only）

## 已验证（2026-08-13 21:43 重定位后）
- ✅ 导入坚果/心血管两条矛盾知识 → 同一 claim
- ✅ 知识地图：2 条目 / 三态 nascent=2（核心视角）
- ✅ 冲突提醒：1 处（子功能）
- ✅ 仲裁 KEEP_A → 年轮 1 条
- ✅ 前端 HTTP 200（知识地图为首屏）

## 技术栈
FastAPI + SQLite + conflict_detector（T002-R3，detector 在线）
