#!/usr/bin/env bash
# vote-archive.sh —— 花火工作室信息归档（每 6 小时，防 ntfy 12h 缓存丢失）
# 归档全部协作 topic → 本地 JSONL + 仓库 docs/archive/（每日快照）
# 用法: vote-archive.sh [--push]
# 默认: 归档到本地 ~/.local/votegate/archive/YYYY-MM-DD/<topic>.jsonl
# --push: 同步当日归档到 acgn-tools 仓库 docs/archive/ 并 push

set -uo pipefail

NTFY="https://ntfy.sh"
ARCHIVE_DIR="$HOME/.local/votegate/archive"
REPO="/home/openclaw/.openclaw/workspace/acgn-tools"
TODAY=$(date +%F)
NOW=$(date '+%Y-%m-%d %H:%M')

TOPICS=(spark-announce spark-board spark-checkin spark-ideas spark-progress spark-requests)

# 发现投票 topic（spark-vote-* 前缀，从已知大会记录）
find_vote_topics() {
  grep -ohE "spark-vote-[A-Za-z0-9]+-[a-f0-9]{4}" "$REPO/agent/meetings/"*.md 2>/dev/null | sort -u
}

archive_topic() {
  local topic="$1"
  local daydir="$ARCHIVE_DIR/$TODAY"
  mkdir -p "$daydir"
  local out="$daydir/$topic.jsonl"
  : > "$out.tmp"  # 临时文件（清空）
  local raw
  raw=$(curl -s --max-time 25 "${NTFY}/${topic}/json?poll=1&since=all") || { echo "  ⚠️ $topic 拉取失败"; return 1; }
  local new_count=0
  echo "$raw" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    local id
    id=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('id',''))" 2>/dev/null)
    [ -z "$id" ] && continue
    if [ ! -f "$out" ] || ! grep -q "\"id\":\"$id\"" "$out" 2>/dev/null; then
      echo "$line" >> "$out.tmp"
      new_count=$((new_count+1))
    fi
  done
  # 合并去重（已有 + 新增）
  if [ -f "$out" ]; then
    cat "$out" >> "$out.tmp" 2>/dev/null
  fi
  # 按 id 去重排序（保留首次出现）
  python3 - "$out.tmp" "$out" <<'PYEOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
seen = set()
out_lines = []
try:
    lines = open(src, encoding='utf-8').read().splitlines()
except FileNotFoundError:
    lines = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        m = json.loads(line)
        mid = m.get('id', '')
    except Exception:
        mid = ''
    if mid and mid in seen:
        continue
    if mid:
        seen.add(mid)
    out_lines.append(line)
with open(dst, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines) + ('\n' if out_lines else ''))
print(len(out_lines))
PYEOF
  local total
  total=$(wc -l < "$out" 2>/dev/null || echo 0)
  rm -f "$out.tmp"
  echo "  ✅ $topic: 累计 $total 条（本次新增 $new_count）"
}

echo "=== 归档 $TODAY $NOW ==="
for t in "${TOPICS[@]}"; do
  archive_topic "$t"
done

echo "--- 投票 topic ---"
for t in $(find_vote_topics); do
  archive_topic "$t"
done

echo "=== 归档完成: $ARCHIVE_DIR/$TODAY ==="
ls -la "$ARCHIVE_DIR/$TODAY/" 2>/dev/null | tail -10

# --push 模式：同步到仓库
if [ "${1:-}" = "--push" ]; then
  echo "=== 同步到仓库 docs/archive/ ==="
  mkdir -p "$REPO/docs/archive"
  cp -r "$ARCHIVE_DIR/$TODAY" "$REPO/docs/archive/"
  cd "$REPO" || exit 1
  git add docs/archive/ 2>/dev/null
  if git diff --cached --quiet; then
    echo "无新增归档内容，跳过 commit"
  else
    git commit -m "spark: T000 archive: 协作信息归档快照 $TODAY（留言板/投票/打卡/提议/进展/公告/请求）" 2>&1 | tail -1
    git push origin main 2>&1 | tail -1
  fi
fi
