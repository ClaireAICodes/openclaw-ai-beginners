# AAR.md - After-Action Review Instructions

**Work autonomously. No need to confirm before starting.**

---

## After-Action Review (AAR) — Instructions

Review recently completed cron jobs and tasks, and write a brief AAR for any that were significant.
You can start by finding all the cron jobs that were run in the past 24 hours and reviewing them. 
- openclaw cron list
- openclaw cron runs --id <job-id> --limit 20

**What counts as significant:**
- Job failed (error status)
- Job took more than a few minutes
- Job produced a meaningful deliverable (git repo, report, etc.)

**For each significant job:**
1. Read its transcript (e.g. session: `agent:main:cron:<job.id>`)
2. Write a short AAR (100-200 words) covering:
   - What we intended
   - What actually happened
   - What went well
   - What didn't and why
   - One concrete improvement for next time
3. Save to `memory/AAR/YYYY-MM-DD_AAR-<job-name>-<job.id>.md` with a tiny YAML header (title, date, task_id, agent, status, score 1-5)
4. Mark it reviewed in `memory/aar-state.json` (track `lastChecked[job.id]`)
5. If it failed or scored low (<3), alert Master Phil with a concise summary of the issue and your fix — no need for full AAR dump.
6. If there are any quick fixes you can work on, just do so autonomously. You don't need permission to proceed. 
7. Iterate and review for each individual job

---
