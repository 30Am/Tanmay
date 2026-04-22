#!/usr/bin/env bash
# Iterate manifest.json, download metadata + subs for each entry sequentially.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Append, don't truncate, so reruns don't lose logs.
echo "=== Run start $(date) ===" >> logs/download.log
echo "=== Run start $(date) ===" >> logs/progress.log

TOTAL=$(python3 -c "import json; print(len(json.load(open('manifest.json'))))")
echo "Total: $TOTAL videos" >> logs/progress.log

python3 -c "
import json
for e in json.load(open('manifest.json')):
    print(e['source'], e['video_id'])
" > logs/work_queue.txt

I=0
while read -r source vid; do
  I=$((I + 1))
  echo "[$I/$TOTAL] $source/$vid $(date '+%H:%M:%S')" >> logs/progress.log
  bash download_batch.sh "$source" "$vid" >> logs/progress.log 2>&1 || echo "FAIL $source/$vid" >> logs/download.errors
done < logs/work_queue.txt

echo "=== Run end $(date) ===" >> logs/progress.log
