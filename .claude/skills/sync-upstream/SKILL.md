---
name: sync-upstream
description: Fetch the latest rAthena upstream and report what changed. Use when the user wants to pull in upstream updates or check how far behind we are. Reports ahead/behind counts, lists conflicting paths in protected directories, and proposes a merge strategy without executing destructive operations.
---

# Sync rAthena upstream

Goal: keep this fork close to `rathena/rathena` master without touching its files. Per `CLAUDE.md`, all customisation lives in overlay points (`npc/custom/`, `conf/import/`, `db/import/`, `sql-files/migrations/`, `data-overlay/`). Upstream paths must never be modified locally.

## Steps

1. **Verify upstream remote**
   - `git remote get-url upstream` — if missing, instruct the user we're still in Phase A and that Phase B will add it via `git remote add upstream https://github.com/rathena/rathena.git`. Stop here.

2. **Fetch upstream**
   - `git fetch upstream master --tags`

3. **Report position**
   - `git rev-list --left-right --count HEAD...upstream/master` to get ahead/behind.
   - `git log --oneline HEAD..upstream/master | head -20` for what's incoming.

4. **Audit for protected-path local edits**
   - Run `git diff --name-only $(git merge-base HEAD upstream/master) HEAD` and flag any path under: `src/`, `conf/` (excluding `conf/import/`), `db/re/`, `db/pre-re/`, `npc/re/`, `npc/pre-re/`, `sql-files/*.sql` (excluding `sql-files/migrations/`).
   - If anything is flagged, this means the discipline was broken in a previous session. Surface it to the user before proceeding — do not silently merge.

5. **Propose merge strategy** (do not execute without user confirmation)
   - If `ahead == 0`: fast-forward — `git merge --ff-only upstream/master`.
   - If `ahead > 0` and customisations are only in overlay points: regular merge or rebase, expect zero conflicts.
   - If protected-path edits exist: stop, report which files, ask user how to reconcile.

6. **Post-merge sanity (only if user approves merge)**
   - `cmake -S . -B build` (or whatever build is configured) to verify it still compiles.
   - Reload-script smoke test if the user has a running map-server.

## Output format
Always return:
- One-line summary: `ahead=N behind=M, protected-path edits=X`
- Incoming commits (truncated to 20)
- Proposed action (do not execute without explicit confirmation)
- Any discipline violations found

## What this skill must NOT do
- Never run `git reset --hard`, `git push --force`, or rewrite history.
- Never edit files under protected paths to resolve conflicts — fix the overlay instead.
- Never bypass hooks or signing.
