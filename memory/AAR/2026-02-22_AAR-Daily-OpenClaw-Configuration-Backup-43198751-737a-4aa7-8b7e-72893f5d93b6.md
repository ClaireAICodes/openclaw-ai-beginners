---
title: "Daily OpenClaw Configuration Backup"
date: 2026-02-22
task_id: 43198751-737a-4aa7-8b7e-72893f5d93b6
agent: backup-agent
status: error
score: 2
---

The scheduled backup script was killed by SIGKILL after ~24.5 minutes, resulting in an incomplete backup.

**Intended:** Execute `/home/ubuntu/.openclaw/workspace/bin/backup-to-gdrive.sh` to upload the entire workspace (excluding `workspace-kamiya`) to Google Drive under `OpenClaw Backups/2026-02-22/`, including all agent session data.

**What happened:** The script successfully uploaded top-level directories: skills, memory, Research, bin, and the identity and cron directories. It also created the agents subfolder structure. While uploading agent sessions (starting with kamiya agent), the process received SIGKILL at ~24.5 minutes. The agents directory was only partially populated: backup-agent's sessions folder was essentially empty (only `sessions.json`), and kamiya's sessions folder contained an unknown number of files (listing showed pagination) but did not complete. The script did not exit normally and did not send the completion summary.

**Why:** Most likely an Out-of-Memory (OOM) condition, causing the kernel OOM killer to terminate the process. The upload of many agent session files is memory-intensive.

**What went well:** The bulk of non-agent data (config files, skills, memory logs, research docs, scripts) was uploaded successfully. The root folder and subdirectories were created correctly. The script's structure and ordering (skills, memory, Research, bin, agents) allowed the most critical data to be saved before the resource-intensive agents phase.

**What didn't:** The agents phase, particularly the numerous small session files, caused resource exhaustion. No retry or resumability logic existed; the script cannot continue from where it left off. Cron delivery of the final status was not triggered because the process died before completion.

**Improvement:** Increase available system memory (add swap if needed) or break the backup into smaller batches (e.g., upload agents separately with a separate cron job). Add resumable uploads (track uploaded files, skip existing). Add preflight memory check and reduce batch size if memory pressure rises. Consider streaming uploads directly from disk rather than loading many into memory.

**Recommendation to Master Phil:** The backup is partially complete but missing agent session data. We should either manually re-run the backup after increasing memory or split it. The `backup-to-gdrive.sh` script may need optimization for large numbers of small files. Alternatively, we could use `rclone` or a native Google Drive sync tool that handles such loads better.
