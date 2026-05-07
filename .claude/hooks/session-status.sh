#!/usr/bin/env bash
# SessionStart hook: report repo state vs rAthena upstream.
# Output is shown to Claude as system context. Keep it short.
set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
echo "[rAthena 私服 session] branch=${branch}"

if git remote get-url upstream >/dev/null 2>&1; then
  # Upstream is configured. Show local position vs cached upstream/master
  # without fetching (fetch is what /sync-upstream is for; keep hook fast).
  if git rev-parse --verify upstream/master >/dev/null 2>&1; then
    ahead=$(git rev-list --count upstream/master..HEAD 2>/dev/null || echo "?")
    behind=$(git rev-list --count HEAD..upstream/master 2>/dev/null || echo "?")
    echo "vs upstream/master: ahead=${ahead} behind=${behind} (cached, run /sync-upstream to refresh)"
  else
    echo "upstream remote configured but upstream/master not fetched yet — run /sync-upstream"
  fi
else
  echo "upstream remote not configured. Phase B will add: git remote add upstream https://github.com/rathena/rathena.git"
fi

# Discipline reminder
echo "Reminder: never edit src/, conf/*.conf (except conf/import/), db/(re|pre-re)/, npc/(re|pre-re)/. See CLAUDE.md."
