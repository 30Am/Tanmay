#!/usr/bin/env bash
# Download metadata (info.json) + Hindi/English subtitles (auto or uploaded) for one video.
# Usage: download_batch.sh <source> <video_id>
set -euo pipefail

SOURCE="$1"
VID="$2"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/raw/$SOURCE/$VID"
mkdir -p "$OUT"

# Skip if already done (info.json present and at least one vtt OR explicit .no_subs marker)
if [ -f "$OUT/$VID.info.json" ] && { ls "$OUT"/*.vtt >/dev/null 2>&1 || [ -f "$OUT/.no_subs" ]; }; then
  echo "skip $SOURCE/$VID"
  exit 0
fi

yt-dlp \
  --skip-download \
  --write-info-json \
  --write-auto-sub \
  --write-sub \
  --sub-lang "hi,en,en-US,en-GB" \
  --convert-subs vtt \
  --no-warnings \
  --no-progress \
  --retries 5 \
  --retry-sleep 'http:exp=1:30' \
  --sleep-requests 1.5 \
  --sleep-subtitles 2 \
  --socket-timeout 30 \
  -o "$OUT/%(id)s.%(ext)s" \
  "https://www.youtube.com/watch?v=$VID" \
  >> "$ROOT/logs/download.log" 2>&1

# Mark no-subs so we don't retry
if [ -f "$OUT/$VID.info.json" ] && ! ls "$OUT"/*.vtt >/dev/null 2>&1; then
  touch "$OUT/.no_subs"
fi

echo "done $SOURCE/$VID"
