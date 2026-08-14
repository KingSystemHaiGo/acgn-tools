#!/usr/bin/env bash
# vote-clerk.sh —— 花火工作室投票书记员（ntfy.sh 公共节点版）
# 用法:
#   vote-clerk.sh stats <topic>              # 拉票→统计→输出票面 JSON
#   vote-clerk.sh report <M编号> <topic>     # 统计→append M00X.md 票面节→输出催票名单
#   vote-clerk.sh open <M编号> <议题描述>    # 生成新投票 topic 名（spark-vote-<M>-<rand4>）
#
# 协议: agent 投票 = curl -d '{"choice":"AGREE","member":"长征","note":"..."}' https://ntfy.sh/<topic>
# choice: AGREE / OPPOSE / ABSTAIN / INFO

set -uo pipefail

NTFY="https://ntfy.sh"
REPO="/home/openclaw/.openclaw/workspace/acgn-tools"

stats() {
  local topic="${1:?用法: vote-clerk.sh stats <topic>}"
  local raw
  raw=$(curl -s --max-time 20 "${NTFY}/${topic}/json?poll=1&since=all") || { echo '{"error":"fetch_failed"}'; exit 1; }
  VOTE_RAW="$raw" python3 - "$topic" <<'PYEOF'
import json, sys, os
lines = os.environ.get('VOTE_RAW', '')
topic = sys.argv[1]
votes = []
agree = oppose = abstain = info = 0
members = {}
for line in lines.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        m = json.loads(line)
    except Exception:
        continue
    if m.get('event') != 'message':
        continue
    body = m.get('message', '')
    try:
        v = json.loads(body)
    except Exception:
        v = {'choice': 'INFO', 'member': 'unknown', 'note': body[:80]}
    choice = str(v.get('choice', 'INFO')).upper()
    member = str(v.get('member', 'unknown'))
    note = str(v.get('note', ''))[:200]
    issue = str(v.get('issue', ''))[:120]
    votes.append({
        'id': m.get('id', ''),
        'ts': m.get('time', 0),
        'member': member,
        'choice': choice,
        'issue': issue,
        'note': note,
    })
    members[member] = choice  # last-wins
    if choice == 'AGREE': agree += 1
    elif choice == 'OPPOSE': oppose += 1
    elif choice == 'ABSTAIN': abstain += 1
    else: info += 1
print(json.dumps({
    'topic': topic,
    'total_raw_messages': len(votes),
    'tally': {'AGREE': agree, 'OPPOSE': oppose, 'ABSTAIN': abstain, 'INFO': info},
    'unique_members': members,
}, ensure_ascii=False, indent=2))
PYEOF
}

report() {
  local mid="${1:?用法: vote-clerk.sh report <M编号> <topic>}"
  local topic="${2:?用法: vote-clerk.sh report <M编号> <topic>}"
  local out
  out=$(stats "$topic")
  # append 到 M00X.md
  local f="$REPO/agent/meetings/${mid}.md"
  if [ -f "$f" ]; then
    {
      echo ""
      echo "## 票面（vote-clerk $(date '+%Y-%m-%d %H:%M')，topic $topic）"
      echo '```json'
      echo "$out"
      echo '```'
    } >> "$f"
    echo "✅ 票面已 append 到 $f"
  else
    echo "⚠️ $f 不存在，票面未落仓"
  fi
  # 输出催票名单（由调用方决定怎么催）
  echo "$out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
tally = d.get('tally', {})
voted = set(d.get('unique_members', {}).keys())
print(f\"票面: 同意{tally.get('AGREE',0)}/反对{tally.get('OPPOSE',0)}/弃权{tally.get('ABSTAIN',0)}/其他{tally.get('INFO',0)}\")
print('已投票:', ', '.join(sorted(voted)) if voted else '无')
"
}

open_topic() {
  local mid="${1:?用法: vote-clerk.sh open <M编号> <议题描述>}"
  shift
  local desc="$*"
  local rand
  rand=$(head -c 4 /dev/urandom | xxd -p | head -c 4)
  echo "spark-vote-${mid}-${rand}"
  echo "议题: $desc"
  echo "投票: curl -d '{\"choice\":\"AGREE|OPPOSE|ABSTAIN|INFO\",\"member\":\"你的名字\",\"note\":\"可选\"}' https://ntfy.sh/spark-vote-${mid}-${rand}"
}

case "${1:-}" in
  stats)  stats "${2:-}" ;;
  report) report "${2:-}" "${3:-}" ;;
  open)   open_topic "${2:-}" "${@:3}" ;;
  *) echo "用法: vote-clerk.sh {stats|report|open} ..."; exit 1 ;;
esac
