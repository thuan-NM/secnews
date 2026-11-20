#!/bin/sh
# Cài các job cron của SecNews (SAD §4): run mỗi 15 phút, digest 08:30 giờ Việt Nam, backup DB hằng ngày.
# Chạy lại nhiều lần vẫn an toàn: dòng cũ có đuôi "# secnews" bị thay bằng dòng mới.
#   sh scripts/install-cron.sh           cài vào crontab của user hiện tại
#   sh scripts/install-cron.sh --print   chỉ in ra, không cài
set -eu

DIR=$(cd "$(dirname "$0")/.." && pwd)
PY="$DIR/.venv/bin/python"
LOCK=/tmp/secnews.lock

# 08:30 giờ VN = 01:30 UTC; đổi sang giờ của máy theo độ lệch `date +%z` (vd. +0000, +0700)
OFF=$(date +%z)
SIGN=$(echo "$OFF" | cut -c1)
OH=$(echo "$OFF" | cut -c2-3 | sed 's/^0//')
OM=$(echo "$OFF" | cut -c4-5)
if [ "$OM" != "00" ]; then
  echo "Timezone lệch $OFF không tròn giờ; tự sửa giờ digest trong crontab." >&2
  exit 1
fi
HOUR=$(( (1 $SIGN ${OH:-0} + 24) % 24 ))
BACKUP_HOUR=$(( (HOUR + 18) % 24 ))   # 02:30 giờ VN, ngoài giờ digest

LINES="*/15 * * * * cd $DIR && flock -n $LOCK $PY -m secnews run >> logs/run.log 2>&1 # secnews
30 $HOUR * * * cd $DIR && flock $LOCK $PY -m secnews digest >> logs/run.log 2>&1 # secnews
30 $BACKUP_HOUR * * * cd $DIR && $PY -c \"import sqlite3; sqlite3.connect('data/secnews.db').backup(sqlite3.connect('data/secnews.backup.db'))\" # secnews"

if [ "${1:-}" = "--print" ]; then
  echo "$LINES"
  exit 0
fi

[ -x "$PY" ] || { echo "Không thấy $PY; tạo venv trước (docs/DEPLOY.md §3)." >&2; exit 1; }
[ -f "$DIR/.env" ] && [ -f "$DIR/config.yaml" ] || { echo "Thiếu .env hoặc config.yaml trong $DIR." >&2; exit 1; }
command -v flock >/dev/null || { echo "Thiếu flock (gói util-linux)." >&2; exit 1; }
mkdir -p "$DIR/logs" "$DIR/data"

TMP=$(mktemp)
{ crontab -l 2>/dev/null | grep -v '# secnews$' || true; echo "$LINES"; } > "$TMP"
crontab "$TMP"
rm -f "$TMP"
echo "Đã cài (timezone máy: $OFF, digest lúc $HOUR:30 giờ máy = 08:30 giờ VN):"
crontab -l | grep '# secnews$'
