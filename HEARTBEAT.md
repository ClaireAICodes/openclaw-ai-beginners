# HEARTBEAT.md

**Work autonomously. No need to confirm before starting.**
**Checkup sometimes on your human during day time**

---

## After-Action Review (AAR) — Heartbeat Instructions

Review your recently completed cron jobs and tasks, and write a brief AAR for any that were significant.

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
6. Otherwise, if there are no new failures or unreviewed tasks, then no alerts are necessary
