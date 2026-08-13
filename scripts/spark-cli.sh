#!/usr/bin/env bash
# spark-cli.sh — 花火工作室项目管理 CLI v0.2
# 双视图仓库：human/（董事会可读）agent/（机器可解析）
# 功能：sync|status|status-json|review|log|submit|review-approve|review-reject|meeting|board|help
set -uo pipefail

REPO_DIR="${SPARK_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REMOTE="origin"
BRANCH="main"

# ── 同步 ──
sync() {
  cd "$REPO_DIR" || exit 1
  git pull --rebase "$REMOTE" "$BRANCH" 2>&1 | tail -2
  echo "✅ synced"
}

# ── 任务状态一览（人类可读）──
status() {
  cd "$REPO_DIR" || exit 1
  echo "=== 花火工作室任务状态 ==="
  for task in "$REPO_DIR"/docs/task-*/; do
    [ -d "$task" ] || continue
    tid=$(basename "$task")
    desc=$(grep -m1 "^# \|^## " "$task/TASK.md" 2>/dev/null | sed 's/^#* //')
    echo "── $tid: $desc"
    grep -A1 "^### T[0-9]" "$task/TASK.md" 2>/dev/null | grep "^### " | sed 's/^/    /'
    rev=$(grep -m1 "^- 状态:" "$task/REVIEWS.md" 2>/dev/null | sed 's/^- 状态: //')
    [ -n "$rev" ] && echo "    最近评审: $rev"
  done
  echo ""
  echo "=== 最近提交 ==="
  git -C "$REPO_DIR" log --oneline -8 2>/dev/null | sed 's/^/  /'
}

# ── Agent 机器可读状态（JSON，供 agent 解析）──
status_json() {
  cd "$REPO_DIR" || exit 1
  {
    echo "{"
    echo "  \"studio\": \"花火工作室\","
    echo "  \"repo\": \"https://github.com/KingSystemHaiGo/acgn-tools\","
    echo "  \"generated_at\": \"$(date '+%Y-%m-%d %H:%M')\","
    echo "  \"tasks\": ["
    first=1
    for task in "$REPO_DIR"/docs/task-*/; do
      [ -d "$task" ] || continue
      [ $first -eq 0 ] && echo ","
      first=0
      tid=$(basename "$task")
      desc=$(grep -m1 "^# \|^## " "$task/TASK.md" 2>/dev/null | sed 's/^#* //')
      rev=$(grep -m1 "^- 状态:" "$task/REVIEWS.md" 2>/dev/null | sed 's/^- 状态: //')
      echo "    {\"id\": \"$tid\", \"desc\": \"$desc\", \"latest_review\": \"${rev:-none}\"}"
    done
    echo "  ],"
    echo "  \"recent_commits\": ["
    git log --oneline -5 2>/dev/null | sed 's/^/    "/; s/$/"/' | tr '\n' ',' | sed 's/,$//'
    echo ""
    echo "  ]"
    echo "}"
  } > agent/STATUS.json
  echo "✅ agent/STATUS.json 已生成（机器可读视图）"
}

# ── 异步大会：发起新会议 ──
meeting_new() {
  local title="${1:-无标题}" agenda="${2:-}"
  cd "$REPO_DIR" || exit 1
  local n
  n=$(ls agent/meetings/ 2>/dev/null | grep -c "^M" || true)
  [ -z "$n" ] && n=0
  local mid="M$(printf '%03d' $((n+1)))"
  local f="agent/meetings/$mid.md"
  cat > "$f" << EOF
# 异步大会 $mid：$title

- 发起人: CEO 小花花
- 发起时间: $(date '+%Y-%m-%d %H:%M')
- 议程: $agenda
- 方式: 点对点异步（各成员在仓库 agent/meetings/$mid.md 追加意见，或私信代录）

## 议程
$agenda

## 成员意见（append-only）
EOF
  git add -A && git commit -m "spark: $mid meeting: 发起异步大会 $title" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ 大会 $mid 已发起（$f）——通知成员后收集意见"
}

# ── 异步大会：记录成员意见 ──
meeting_comment() {
  local mid="${1:-}" member="${2:-}" opinion="${3:-}"
  [ -z "$mid" ] && echo "用法: spark-cli.sh meeting comment <M编号> <成员> <意见>" && exit 1
  cd "$REPO_DIR" || exit 1
  local f="agent/meetings/$mid.md"
  [ -f "$f" ] || { echo "大会不存在: $f"; exit 1; }
  {
    echo ""
    echo "- [$member] $opinion"
  } >> "$f"
  git add -A && git commit -m "spark: $mid update: $member 意见" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ $member 意见已记录"
}

# ── 异步大会：汇总决议 ──
meeting_decide() {
  local mid="${1:-}" decision="${2:-}"
  [ -z "$mid" ] && echo "用法: spark-cli.sh meeting decide <M编号> <决议>" && exit 1
  cd "$REPO_DIR" || exit 1
  local f="agent/meetings/$mid.md"
  [ -f "$f" ] || { echo "大会不存在: $f"; exit 1; }
  {
    echo ""
    echo "## 决议"
    echo "- 时间: $(date '+%Y-%m-%d %H:%M')"
    echo "- 决议: $decision"
  } >> "$f"
  # 决议同时进 human/decisions（董事会可读）
  local df="human/decisions/$mid-$(date '+%Y%m%d').md"
  cat > "$df" << EOF
# 决议 $mid（$decision 前 30 字…）

- 日期: $(date '+%Y-%m-%d')
- 会议: $mid
- 决议: $decision
- 全文: 见 agent/meetings/$mid.md
EOF
  git add -A && git commit -m "spark: $mid decide: $decision" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ 决议已记录（agent/meetings/$mid.md + human/decisions/）"
}

# ── 董事会汇报（人类可读，定期）──
board_report() {
  cd "$REPO_DIR" || exit 1
  local today=$(date '+%Y-%m-%d')
  local f="human/board/$today.md"
  {
    echo "# 花火工作室董事会汇报（$today）"
    echo ""
    echo "## 一、本周期进展"
    git log --oneline --since="24 hours ago" 2>/dev/null | sed 's/^/  - /'
    echo ""
    echo "## 二、任务状态"
    ./scripts/spark-cli.sh status 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "## 三、待董事会决策事项"
    echo "  （待填）"
    echo ""
    echo "## 四、风险与需支持"
    echo "  （待填）"
  } > "$f"
  git add -A && git commit -m "spark: T000 board: 董事会汇报 $today" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ 董事会汇报已生成: human/board/$today.md"
}

review() {
  local tid="${1:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh review <任务ID>" && exit 1
  local taskdir=$(echo "$tid" | sed 's/-T[0-9]*$//' | sed 's/^T/task-/' | tr 'A-Z' 'a-z')
  local f="$REPO_DIR/docs/$taskdir/REVIEWS.md"
  if [ -f "$f" ]; then cat "$f"; else echo "未找到 $f（先 ./spark-cli.sh sync）"; fi
}

log() { git -C "$REPO_DIR" log --oneline -20 2>/dev/null | sed 's/^/  /'; }

submit() {
  local tid="${1:-}" desc="${2:-}"
  [ -z "$tid" ] && echo "用法: spark-cli.sh submit <任务ID> <描述>" && exit 1
  cd "$REPO_DIR" || exit 1
  git add -A
  git commit -m "spark: $tid deliver: $desc" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ submitted $tid"
}

review_approve() { review_impl "$1" "APPROVED" "$2"; }
review_reject() { review_impl "$1" "REJECTED" "$2"; }

review_impl() {
  local tid="$1" st="$2" verdict="$3"
  local taskdir=$(echo "$tid" | sed 's/-T[0-9]*$//' | sed 's/^T/task-/' | tr 'A-Z' 'a-z')
  local dir="$REPO_DIR/docs/$taskdir"
  mkdir -p "$dir"
  local f="$dir/REVIEWS.md"
  [ -f "$f" ] || echo "# $taskdir 评审记录（append-only）" > "$f"
  {
    echo ""
    echo "## $tid review ($(date '+%Y-%m-%d %H:%M') by ${SPARK_REVIEWER:-$(git config user.name 2>/dev/null || echo unknown)})"
    echo "- 状态: $st"
    echo "- 结论: $verdict"
  } >> "$f"
  cd "$REPO_DIR" || exit 1
  git add -A
  git commit -m "spark: $tid review-$([ "$st" = APPROVED ] && echo approve || echo reject): $verdict" 2>&1 | tail -1
  git push "$REMOTE" "$BRANCH" 2>&1 | tail -1
  echo "✅ review $st on $tid"
}

help() {
  echo "花火工作室项目管理 CLI v0.2（双视图仓库：human/ 董事会 + agent/ 机器）"
  echo "用法:"
  echo "  ./spark-cli.sh sync                    # 拉取最新"
  echo "  ./spark-cli.sh status                  # 任务状态（人类可读）"
  echo "  ./spark-cli.sh status-json             # 机器可读状态 → agent/STATUS.json"
  echo "  ./spark-cli.sh review <任务ID>         # 看评审"
  echo "  ./spark-cli.sh log                     # 最近提交"
  echo "  ./spark-cli.sh submit <任务ID> <描述>  # 提交产物"
  echo "  ./spark-cli.sh review-approve|reject <任务ID> <结论>"
  echo "  ./spark-cli.sh meeting new <标题> <议程>           # 发起异步大会"
  echo "  ./spark-cli.sh meeting comment <M编号> <成员> <意见> # 记录意见"
  echo "  ./spark-cli.sh meeting decide <M编号> <决议>        # 汇总决议"
  echo "  ./spark-cli.sh board                   # 生成董事会汇报"
}

case "${1:-}" in
  sync) sync ;;
  status) status ;;
  status-json) status_json ;;
  review) review "${2:-}" ;;
  log) log ;;
  submit) submit "${2:-}" "${3:-}" ;;
  review-approve) review_approve "${2:-}" "${3:-}" ;;
  review-reject) review_reject "${2:-}" "${3:-}" ;;
  meeting)
    case "${2:-}" in
      new) meeting_new "${3:-}" "${4:-}" ;;
      comment) meeting_comment "${3:-}" "${4:-}" "${5:-}" ;;
      decide) meeting_decide "${3:-}" "${4:-}" ;;
      *) echo "meeting 子命令: new|comment|decide" ;;
    esac ;;
  board) board_report ;;
  *) help ;;
esac
