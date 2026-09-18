#!/usr/bin/env bash
# M1 一键起跑 —— 个人知识宇宙 MVP（花火工作室 / acgn-tools）
# 用法：bash scripts/run.sh   （可选 PORT=8000）
# 验收：新机器 clone 后执行本脚本 → 浏览器打开 http://localhost:$PORT 可用（首屏=知识地图）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/apps/knowledge-map"
PORT="${PORT:-8000}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[run.sh] 需要 uv（https://docs.astral.sh/uv/）。未找到 uv，请先安装。" >&2
  exit 1
fi

cd "$APP"

if [ ! -x .venv/bin/python ]; then
  echo "[run.sh] 首次运行，同步依赖（uv sync）..."
  uv sync
fi

echo "[run.sh] 启动 http://localhost:$PORT （Ctrl-C 退出）"
exec .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port "$PORT"
