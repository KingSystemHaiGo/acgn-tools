#!/usr/bin/env bash
# spark-cli.sh — 花火工作室项目管理 CLI v0.1
# 从远程仓库读任务状态/评审意见，提交产物/评审（统一信息格式）
# 用法: ./spark-cli.sh <status|review|log|submit|review-approve|review-reject|sync|help>
set -uo pipefail

REPO_DIR="${SPARK_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REMOTE="origin"
BRANCH="main"

# 同步最新状态
sync() {
  cd "$REPO_DIR" || exit 1
  git pull --rebase "$REMOTE" "$BRANCH" 2>&1 | tail -3
  echo "✅ synced"
}

# 所有任务状态一览（从 docs/task-*/TASK.md 标题 + REVIEWS.md 状态解析）
status() {
  cd "$REPO_DIR" || exit 1
  echo "=== 任务状态一览 ==="
  for task in "$REPO_DIR"/docs/task-*/; do
    [ -d "$task" ] || continue
    tid=$(basename "$task")
    desc=$(grep -m1 "^# \|^## " "$task/TASK.md" 2>/dev/null | sed 's/^#* //')
    # 各子任务状态
    echo "── $tid: $desc"
    grep -A1 "^### T[0-9]" "$task/TASK.md" 2>/dev/null | grep "^### " | sed 's/^/    /'
    # 最近评审
    rev=$(grep -m1 "^- 状态:" "$task/REVIEWS.md" 2>/dev/null | sed 's/^- 状态: //')
    [ -n "$rev" ] && echo "    最近评审: $rev"
  done
  echo ""
  echo "=== 最近提交 ==="
  git -C "$REPO_DIR" log --oneline -10 2>/dev/null | sed 's/^/  /'
}

# 看某任务评审意见
review() {
  local tid="${1:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh review <任务ID>" && exit 1
  local f="$REPO_DIR/docs/$tid/REVIEWS.md"
  if [ -f "$f" ]; then
    cat "$f"
  else
    echo "未找到 $f（先 ./spark-cli.sh sync）"
  fi
}

# 最近提交流水
log() {
  cd "$REPO_DIR" || exit 1
  git log --oneline -20 2>/dev/null | sed 's/^/  /'
}

# 提交产物（当前目录变更，统一提交消息格式）
submit() {
  local tid="${1:-}" desc="${2:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh submit <任务ID> <描述>" && exit 1
  cd "$REPO_DIR" || exit 1
  git add -A
  git commit -m "spark: $tid deliver: $desc" 2>&1 | tail -2
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -2
  echo "✅ submitted $tid"
}

# 评审通过（append 到 REVIEWS.md + 提交）
review_approve() {
  local tid="${1:-}" verdict="${2:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh review-approve <任务ID> <结论>" && exit 1
  review_impl "$tid" "APPROVED" "$verdict"
}

# 评审驳回
review_reject() {
  local tid="${1:-}" verdict="${2:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh review-reject <任务ID> <结论>" && exit 1
  review_impl "$tid" "REJECTED" "$verdict"
}

review_impl() {
  local tid="$1" st="$2" verdict="$3"
  local dir="$REPO_DIR/docs/$tid"
  mkdir -p "$dir"
  local f="$dir/REVIEWS.md"
  [ -f "$f" ] || echo "# $tid 评审记录（append-only）" > "$f"
  {
    echo ""
    echo "## $tid review ($(date '+%Y-%m-%d %H:%M') by ${SPARK_REVIEWER:-$(git config user.name 2>/dev/null || echo unknown)})"
    echo "- 状态: $st"
    echo "- 结论: $verdict"
    echo "- 下一步: 见仓库 docs/$tid/TASK.md"
  } >> "$f"
  cd "$REPO_DIR" || exit 1
  git add -A
  git commit -m "spark: $tid review-$([ "$st" = APPROVED ] && echo approve || echo reject): $verdict" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ review $st on $tid"
}

help() {
  grep "^# " "$0" | head -3
  echo "用法:"
  echo "  ./spark-cli.sh sync               # 拉取最新"
  echo "  ./spark-cli.sh status             # 任务状态一览"
  echo "  ./spark-cli.sh review <任务ID>    # 看评审意见 (如 T001-T1)"
  echo "  ./spark-cli.sh log                # 最近提交"
  echo "  ./spark-cli.sh submit <任务ID> <描述>      # 提交产物"
  echo "  ./spark-cli.sh review-approve <任务ID> <结论>"
  echo "  ./spark-cli.sh review-reject <任务ID> <结论>"
}

case "${1:-}" in
  sync) sync ;;
  status) status ;;
  review) review "${2:-}" ;;
  log) log ;;
  submit) submit "${2:-}" "${3:-}" ;;
  review-approve) review_approve "${2:-}" "${3:-}" ;;
  review-reject) review_reject "${2:-}" "${3:-}" ;;
  *) help ;;
esac
