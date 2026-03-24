# AAR — Daily OpenClaw Configuration Backup
**Job ID:** 7458e079-8b91-4aa8-a864-9639291eb173
**Date:** 2026-03-17
**Run Time:** 06:00 UTC (14:00 SGT)
**Duration:** 767s (12.8 min) — ANOMALOUSLY LONG
**Status:** ✅ OK

## What Happened
Backup completed successfully but took 12.8 minutes. Summary indicates the script was still uploading skills with git histories and node_modules.

## Performance Concern
Normal backup should complete in 2-5 minutes for config-only. The job is including:
- All skills with full `.git` histories
- `node_modules` directories from each skill
- This creates thousands of small files

## Historical Pattern
This job has a troubled history:
- Mar 15: OK (748s)
- Mar 14: OK (431s — used free model, hallucinated monitoring)
- Mar 13: OK (768s)
- Mar 12: TIMEOUT (30 min exceeded)
- Mar 11: Error — bash array subscript bug
- Mar 10: Error — bash array subscript bug
- Mar 9: SIGTERM timeout
- Earlier: Missing exec capabilities, message delivery failures

The job now runs with `hunter-alpha` model and exec access — major improvement over earlier failures.

## Recommendations
1. Exclude `node_modules` from backup (can be reinstalled via npm/yarn)
2. Consider shallow git clones for skills (depth=1) to reduce backup size
3. Set timeout to 20+ minutes to avoid timeouts on large backups

## Action Items
- Review backup script: `/home/ubuntu/.openclaw/workspace/bin/backup-to-gdrive.sh`
- Consider excluding node_modules and .git from backup scope
