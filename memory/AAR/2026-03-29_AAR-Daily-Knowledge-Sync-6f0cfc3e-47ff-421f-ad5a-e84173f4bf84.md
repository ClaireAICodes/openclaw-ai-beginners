---
title: "Daily Knowledge Sync - Missing km Command"
date: 2026-03-29
task_id: 6f0cfc3e-47ff-421f-ad5a-e84173f4bf84
agent: main
status: error
score: 1
---

## After-Action Review

**Intended:** Run `km sync --days_back 7` daily to synchronize memory entries into the structured knowledge base (`memory/KM/`), categorizing content by type and maintaining sync state.

**Actual:** The cron job failed immediately because the `km` command was not found in the system PATH. No synchronization occurred. The error indicates that the knowledge management CLI tool is either not installed, not in the expected location, or the cron environment's PATH differs from interactive shells.

**What went well:** N/A — the job did not execute.

**What didn't and why:** The `km` binary is missing or inaccessible to the cron environment. This could be due to: (1) the knowledge-management skill not providing a CLI binary, (2) the binary being installed in a user-local directory (e.g., `~/.local/bin`) that isn't in cron's PATH, or (3) the cron job configuration not using the full path to the command.

**One concrete improvement:** Update the cron job to use the absolute path to the `km` executable (e.g., `/home/node/.local/bin/km` or `/usr/local/bin/km`). To find the correct path, run `which km` in an interactive session where the tool works. If the tool is not installed at all, install the knowledge-management skill or create a wrapper script that sets up the environment before invoking the tool. Additionally, add a pre-check in the cron script that verifies command availability and sends an alert if not found, to avoid silent failures.
