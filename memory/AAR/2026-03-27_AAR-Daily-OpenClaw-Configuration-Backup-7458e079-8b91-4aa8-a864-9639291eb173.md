---
title: "Daily OpenClaw Configuration Backup - Failure"
date: 2026-03-27
task_id: 7458e079-8b91-4aa8-a864-9639291eb173
agent: main
status: failed
score: 2
---

## What we intended

The Daily OpenClaw Configuration Backup job is designed to back up critical configuration files and workspace data to Google Drive. This includes top-level files (openclaw.json, SOUL.md, USER.md, MEMORY.md, etc.), the agents directory, cron jobs, identity files, and important subdirectories like memory, Research, bin, skills, and workshops. The backup runs daily to ensure we have off-site copies of all configuration and code.

## What actually happened

The backup script started correctly and began creating the folder structure on Google Drive. It uploaded all top-level configuration files successfully and proceeded to upload subdirectories. However, a bug in the `create_folder` function (line 101) caused intermittent failures where the folder creation appeared to succeed but no folder ID was captured from the JSON output. Despite the script's retry logic and recovery mechanisms (it would later find the already-created folders), these errors cluttered the logs and may have contributed to inefficiency.

More critically, the backup attempted to include the entire `skills` directory, which contains Git metadata (`.git` folders). This vastly increased the number of files and total upload size. The script ran for approximately 60 minutes before hitting the cron job timeout and being terminated, leaving the backup incomplete. No housekeeping (deduplication, old backup cleanup) was performed.

## What went well

- The script created the destination folder hierarchy correctly
- Top-level configuration files uploaded without issue
- The retry and recovery logic worked: even when folder creation appeared to fail, the script would later discover the folder existed and continue
- Logging was clear with timestamps, making it easy to trace progress
- The script properly used the `gog` CLI with retries for network resilience
- Upload of many files from skills/ subdirectories proceeded correctly

## What didn't and why

**Primary failure: Bug in folder ID capture**

In the `create_folder` function, the line:
```bash
local json
if [[ -z "$parent_id" ]]; then
  json=$(gog_retry drive mkdir "$name" --json) || { error "Failed to create folder: $name"; return 1; }
else
  json=$(gog_retry drive mkdir "$name" --parent="$parent_id" --json) || { error "Failed to create folder: $name under $parent_id"; return 1; }
fi
local id
id=$(echo "$json" | $JQ_CMD -r '.folder.id')
```

The error `/home/node/.openclaw/workspace/bin/backup-to-gdrive.sh: line 101: : command not found` suggests that `$JQ_CMD` might be empty or the `jq` command is not found. However, `JQ_CMD` was set to `/home/linuxbrew/.linuxbrew/bin/jq`. The blank command indicates that `echo "$json"` might have produced empty output, or the pipe to `$JQ_CMD` was interpreted as an empty command due to variable expansion failure. Regardless, the script continued because the error happened in a subshell and the `id` check later would catch it, but the error message itself and the inability to capture the ID correctly caused the script to take a slower path (retry via lookup).

**Secondary failure: Excessive runtime**

The backup included the `skills` directory with its `.git` subdirectories. The `.git` metadata contains many small files (hooks, objects, refs, logs, etc.) that dramatically increase the number of files to upload. This caused the total upload time to exceed the cron job's 60-minute timeout. The script itself has no internal timeout; it would have eventually completed if not killed externally.

## One concrete improvement for next time

**Fix the JSON parsing bug and exclude `.git` directories from backup.**

1. **Fix the `create_folder` function** by ensuring `$JQ_CMD` is properly quoted and handling empty JSON:
   ```bash
   id=$(echo "$json" | "$JQ_CMD" -r '.folder.id' 2>/dev/null || true)
   if [[ -z "$id" || "$id" == "null" ]]; then
     error "Create folder succeeded but no ID returned for $name (JSON: ${json:0:100})"
     return 1
   fi
   ```
   Also add quoting around `$JQ_CMD` to handle spaces.

2. **Exclude `.git` directories** from the backup by modifying the script to skip any directory named `.git` during the recursive upload phase. This will drastically reduce the number of files and total transfer size, preventing timeout. Add early in the upload loops:
   ```bash
   [[ "$file" == *"/.git/"* ]] && continue
   ```

3. **Increase the cron job timeout** to allow up to 2-3 hours for backup to complete, in case unexpected large files are encountered.

Implementing these changes will make the backup reliable and fast.