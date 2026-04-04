---
title: Daily OpenClaw Configuration Backup - Failed (Timeout + Script Bug)
date: 2026-04-03
task_id: 7458e079
agent: main
status: error
score: 1
---

**Intended:** Execute /home/node/.openclaw/workspace/bin/backup-to-gdrive.sh to back up OpenClaw configuration and workspace to Google Drive, creating a dated folder and uploading all critical files including .git histories. The script should run within 15 minutes, handle errors with retries, and send a summary report on success.

**What happened:** The script started at 22:00 UTC and ran for about 15 minutes. It encountered recurring parsing errors on line 101 (`: command not found`) during folder creation, causing many nested .git subdirectories to fail uploading due to missing folder IDs. Despite these errors, the script continued and uploaded some top-level config files and partial skill directories. However, the script exceeded its 900-second timeout and was killed by SIGTERM before completing housekeeping steps (deduplication, old backup cleanup). The backup is incomplete.

**What went well:** Some critical configuration files (openclaw.json, AGENTS.md, SOUL.md, etc.) were successfully uploaded. The script continued despite errors rather than crashing immediately, allowing partial backup.

**What didn't:** The root cause is a bug on line 101 inside `create_folder()`: `id=$(echo "$json" | $JQ_CMD -r '.folder.id')`. The `: command not found` error suggests a stray carriage return or hidden character in the script, causing the command substitution to fail. Additionally, the script treats all failures as non-fatal and continues, which led to a very long run time and eventual timeout.

**Improvement:** 
1. Immediately fix line 101: run `dos2unix` on the script or remove any CR characters; ensure clean line endings.
2. Make the script abort early on critical failures (e.g., folder creation) to avoid running for hours with many errors.
3. Increase the timeout for this backup (maybe 30-60 minutes) or break the backup into smaller batches.
4. Consider excluding .git directories from backup, as they are large and can be regenerated from GitHub; this would drastically reduce size and time.
5. Add better error reporting and a final summary sent via Telegram even on partial failures.

**Alert to Master:** The backup failed due to a script bug and timeout. Recommend fixing the script's line endings and increasing the timeout. Partial backup exists but lacks .git histories.
