#!/usr/bin/env bash
# vote-enc.sh —— 花火工作室 ntfy 加密发布（AES-256-GCM，duke 2026-08-14 指示「ntfy 加密，dashboard 解密」）
# 用法:
#   vote-enc.sh pub <topic> '<json或文本>'      # 加密并发布到 ntfy
#   vote-enc.sh enc '<json或文本>'              # 仅加密输出（供调试）
#   vote-enc.sh dec '<base64密文>'              # 解密（验证用）
#   vote-enc.sh key                             # 显示密钥 base64
#
# 原理: agent 之间真实通信走 EigenFlux 私有通道；ntfy 公共 topic 只承载 dashboard 展示数据，
#       数据加密后即使被探测到也只是密文；dashboard（人类查看）持密钥解密展示。

set -uo pipefail

KEY_FILE="$HOME/.local/votegate/key.bin"
NTFY="https://ntfy.sh"

encrypt() {
  local plain="$1"
  VOTE_KEY_B64=$(base64 < "$KEY_FILE" | tr -d '\n') python3 - "$plain" <<'PYEOF'
import os, base64, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = base64.b64decode(os.environ['VOTE_KEY_B64'])
iv = os.urandom(12)
ct = AESGCM(key).encrypt(iv, sys.argv[1].encode('utf-8'), None)
print(base64.b64encode(iv + ct).decode())
PYEOF
}

decrypt() {
  local enc="$1"
  VOTE_KEY_B64=$(base64 < "$KEY_FILE" | tr -d '\n') python3 - "$enc" <<'PYEOF'
import base64, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = base64.b64decode(os.environ['VOTE_KEY_B64'])
raw = base64.b64decode(sys.argv[1])
iv, ct = raw[:12], raw[12:]
print(AESGCM(key).decrypt(iv, ct, None).decode('utf-8'))
PYEOF
}

case "${1:-}" in
  pub)
    topic="${2:?用法: vote-enc.sh pub <topic> '<内容>'}"
    content="${3:?用法: vote-enc.sh pub <topic> '<内容>'}"
    enc=$(encrypt "$content")
    curl -s --max-time 20 -d "$enc" "${NTFY}/${topic}" | head -c 200
    echo ""
    echo "✅ 已加密发布到 ${topic}"
    ;;
  enc) encrypt "${2:-}" ;;
  dec) decrypt "${2:-}" ;;
  key) base64 < "$KEY_FILE" | tr -d '\n' ; echo ;;
  *) echo "用法: vote-enc.sh {pub|enc|dec|key} ..."; exit 1 ;;
esac
