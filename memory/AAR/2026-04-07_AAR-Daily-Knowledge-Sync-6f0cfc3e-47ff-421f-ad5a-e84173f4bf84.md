---
title: "Daily Knowledge Sync"
date: 2026-04-07
task_id: "6f0cfc3e-47ff-421f-ad5a-e84173f4bf84"
agent: "main"
status: "error"
score: 1
---

The Daily Knowledge Sync job (km sync --days_back 7) failed with an upstream Alibaba rate limit error. The job started, performed initial checks (memory search, locating the km command), then attempted to call the qwen/qwen3.6-plus:free model and received a 429 error: "Upstream error from Alibaba: Request rate increased too quickly." The job terminated after ~16 seconds.

What went well: The error was captured cleanly and reported; the initial diagnostic (checking for the km binary) proceeded correctly.

What didn't: The selected free model (qwen) is heavily rate-limited during concurrent cron runs. The burst of multiple cron jobs using the same model exceeds Alibaba's free tier limits, causing early failures.

Improvement: Switch the job's model to openrouter/stepfun/step-3.5-flash:free, which has proven reliable for other cron jobs (Morning Plan Generator, Critical Content Review). Alternatively, add a personal OpenRouter API key to increase quotas or stagger job schedules to reduce concurrency.
