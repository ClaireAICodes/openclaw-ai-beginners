---
title: "⚡ Performance Benchmarks"
content_type: "Research"
domain: "AI Models"
certainty: "Verified"
impact: "Medium"
confidence_score: 8
tags: ["FreeTier", "Benchmark", "Automation"]
source: "daily"
source_file: "2026-02-21.md"
date: "2026-02-21"
content_hash: "1b46023cea6d6665"
---

- Summarization agent: 14 req/min, 3.2s median latency (production-ready)
- Data extraction agent: 8 req/min (multi-step tool calls slower)
- **Warning:** "Free tier" APIs often have 150+ queue → unusable for production
- Hardware bottleneck: Mac RAM bandwidth impacts inference (3.5s/token → fixable to 100+ t/s with tuning)