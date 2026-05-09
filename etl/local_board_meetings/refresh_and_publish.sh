#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

/usr/bin/python3 -m etl.local_board_meetings.runner --log-level WARNING

cp data/local_board_meetings/public/index.html docs/index.html
cp data/local_board_meetings/public/calendar.ics docs/calendar.ics

git add docs/index.html docs/calendar.ics \
  data/local_board_meetings/source_registry.csv \
  data/local_board_meetings/progress_log.md

if git diff --cached --quiet; then
  echo "No calendar changes to publish."
else
  git commit -m "Refresh local board meeting calendar"
  git push origin main
fi
