---
title: "Daily OpenClaw Configuration Backup - Partial Failure"
date: 2026-04-01
task_id: 7458e079-8b91-4aa8-a864-9639291eb173
agent: main
status: error
score: 2
---

## Intended Outcome
The daily backup script (`backup-to-gdrive.sh`) was scheduled to run at 22:00 UTC on April 1st, 2026. Its purpose is to create a complete backup of the entire OpenClaw workspace (including configuration files, skills repositories, memory logs) to Google Drive with proper folder structure and deduplication.

## What Actually Happened
The script executed and ran for approximately 4 minutes and 44 seconds (22:00:16 to 22:05:00 UTC) before receiving a SIGTERM signal and terminating prematurely.

**Successes:**
- Core configuration files were successfully uploaded: `openclaw.json`, `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `MEMORY.md`
- Daily backup folder structure was created on Google Drive: `OpenClaw Backups/2026-04-01/`
- Partial upload of skill repositories: some files from `exa-tool` and `crypto-reporter` skills

**Failures:**
- Script encountered a persistent bug at **line 101** causing `: command not found` errors repeatedly
- Folder ID capture mechanism failed during nested directory creation
- Git objects upload was incomplete - many `.git` files were skipped
- No final summary report was produced due to premature termination
- Backup estimated only 40-50% complete when killed

**Root Cause:**
The `backup-to-gdrive.sh` script has a syntax error on line 101 that prevents proper JSON parsing of folder IDs from the `gog` command output. While the script includes recovery logic to find folders after creation, this becomes unreliable with deeply nested `.git` directory structures containing thousands of small files.

## What Went Well
- The script's error recovery mechanism allowed it to continue despite the line 101 bug
- Critical configuration files were backed up early and are safe
- Google Drive folder structure was established correctly
- The cron job monitoring detected the failure and the session was captured
- No data corruption occurred - just incomplete backup

## What Didn't Work and Why
1. **Line 101 bug:** Empty command execution likely from a malformed pipe or redirection statement. This broke the folder ID extraction logic.
2. **Timeout/kill:** The process was terminated by SIGTERM after ~5 minutes. This could be due to:
   - Cron job timeout enforcement
   - External monitoring terminating long-running jobs
   - Manual intervention
3. **Large .git directories:** The backup includes full Git repositories with objects/refs. These contain thousands of tiny files, making them slow to process and prone to the folder ID capture failures.
4. **No resume capability:** The script doesn't support resuming interrupted backups; it starts from scratch each time.

## Concrete Improvement for Next Time
**Action:** Fix the script's folder creation logic at line 101 in `/home/node/.openclaw/workspace/bin/backup-to-gdrive.sh` and add `.git/objects` and `.git/refs` to the exclusion list (backup only the repository metadata, not the full object store). Additionally, implement:
- Proper timeout configuration matching the backup duration needs
- Progress checkpointing to enable resume capability
- Splitting the backup into two phases: configs (daily) and skills (weekly)
- Better logging to capture exactly where failures occur

**Priority:** HIGH - Backup integrity is critical for disaster recovery. The current 40-50% completeness leaves significant gaps in our data protection.
