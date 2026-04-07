---
title: "Daily Configuration Backup — Catastrophic Token Explosion & Edit Failure"
date: "2026-04-05"
task_id: "7458e079-8b91-4aa8-a864-9639291eb173"
agent: backup-agent
status: "error"
score: 1
---

# AAR: Daily OpenClaw Configuration Backup — Token Explosion & Edit Failure

## Intent
Automated daily backup of `/home/node/.openclaw/workspace` to Google Drive via `backup-to-gdrive.sh`. The cron job monitors execution and alerts on failure.

## What Actually Happened
The latest run (April 5, ~06:00 SGT) failed with **"Edit failed"** after consuming **5,104,743 input tokens and 49,799 output tokens** over 36 minutes. The summary output was just the word "Now" — indicating the monitoring session collapsed under context weight or hit an API error during output generation.

## What Went Well
- Core config files remain backed up in Google Drive from earlier successful runs
- The script itself executes (line 101 bug is non-fatal, folders still get created)
- Delivery to Telegram was achieved despite the error

## What Didn't and Why

### Critical Issue: Token Explosion
Input tokens have grown exponentially over the past 3 days:
- Apr 1: 269K input tokens
- Apr 2: 566K input tokens  
- Apr 3: 658K input tokens
- Apr 4: **5.1M input tokens** (≈8× increase)

**Root cause:** The monitoring agent accumulates the full backup log output as context with every poll cycle. Over 36 minutes of polling, the session history ballooned to ~145K total tokens. By the final turn, the context window was dominated by thousands of file upload log lines, causing model confusion and eventual failure to produce valid output.

### Secondary Issue: Line 101 Bug Still Unfixed
The `create_folder` function in `backup-to-gdrive.sh` continues to fail at line 101 (`: command not found`), likely a CRLF or whitespace issue. While non-fatal (folders get created via recovery logic), it causes double API calls for every folder and slows the backup by 2-3×.

### Tertiary Issue: Backup Duration
36 minutes is excessively long for a monitoring task. The cron should either have a tighter timeout or use a different monitoring approach.

## One Concrete Improvement
**Immediate:** Switch the backup monitoring from interactive polling to passive exec-wait mode. Instead of the agent polling every minute and accumulating log output, launch the script in the background with `exec background=true`, then check the exit code at completion. This reduces token consumption from millions to thousands.

**Secondary:** Fix line 101 in `backup-to-gdrive.sh` — `dos2unix` or manual whitespace cleanup in the `create_folder` function.

**Tertiary:** Add an explicit `timeoutSeconds: 1800` to the cron job payload so the agent session itself times out before model costs explode.

## Alerting Status
Master Phil was already notified of this failure via the cron delivery system. However, the chronic nature (3 consecutive days of escalating failures) warrants a pattern alert — this is not a blip, it's a systemic issue that will continue to waste tokens and money until fixed.
