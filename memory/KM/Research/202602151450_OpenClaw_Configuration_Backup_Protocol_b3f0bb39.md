---
title: "OpenClaw Configuration Backup Protocol"
content_type: "Research"
domain: "AI Models"
certainty: "Verified"
impact: "Medium"
confidence_score: 10
tags: ["AI", "FreeTier", "Automation"]
source: "MEMORY.md"
source_file: "MEMORY.md"
date: "2026-02-15"
content_hash: "b3f0bb392f2ce60a"
---

Established: 2026-02-15
Description: Robust daily backup of all OpenClaw configuration and workspace data to Google Drive using a dedicated script with deduplication, cleanup, and reliable model routing.

**Components:**
- Backup script: `/home/node/.openclaw/workspace/backup-to-gdrive.sh`
- Cron job: `Daily OpenClaw Configuration Backup` (ID: 43198751-737a-4aa7-8b7e-72893f5d93b6)
- Destination: Google Drive folder "OpenClaw Backups/YYYY-MM-DD"
- Model: `cloudflare-ai-gateway/claude-sonnet-4-5` (paid, reliable)

**Coverage:**
- Top-level files: `openclaw.json`, all workspace core markdown (AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md)
- Directories: `workspace/memory`, `workspace/Research`, `workspace/bin`, `workspace/skills`, `agents`, `identity`, `cron`

**Features:**
- Deduplication of files and subfolders within each backup
- Automatic cleanup of backups older than 30 days
- Retry logic with exponential backoff for uploads
- Telegram summary report with success/failure counts
- Executed via `exec` tool by a dedicated isolated agent

**Rationale:**
The previous backup used free-tier models that were unreliable due to rate limits. Switching to a paid model with a robust external script ensures consistent, hands-off backups with full coverage and housekeeping.