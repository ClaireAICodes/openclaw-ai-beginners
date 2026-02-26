---
title: "Critical Findings (New since last run)"
content_type: "Decision"
domain: "AI Models"
certainty: "Verified"
impact: "High"
confidence_score: 8
tags: ["AI", "FreeTier", "Cost", "Automation", "Decision"]
source: "daily"
source_file: "2026-02-13.md"
date: "2026-02-13"
content_hash: "8fb1b6ab7ae87243"
---

**Security Crisis:**
- **42,665 exposed OpenClaw instances** found on Shodan
- 93.4% have authentication bypasses
- 8 instances completely open (no password, full shell access, visible API keys)
- Credentials had been leaking for 11 days in one documented case

**Cost Optimization Breakthroughs:**
- Prompt caching achieves **99x speedup** on M3 Ultra Mac Studio
- Tiered model routing: 75% cheap models (MiMo/Devstral), 15% Haiku, 10% Sonnet, <5% Opus
- Multi-agent architecture demonstrated **70% token reduction** and **77% cost savings**
- Session + memory pruning can eliminate 111KB of context waste per prompt

**Real Revenue Signals:**
- Early adopters: $3,600/month (first month), $15K+ in weeks, 5-figure deals by day 5
- "Done-for-you" setups: $1.5K-$7.5K per client
- Freelance AI automation: $75-150/hr
- Content + affiliate flywheel gaining traction

**Technical Advances:**
- PolyClaw skill for Polymarket trading + arbitrage
- LoomLay plugin: 29 native multi-chain tools with self-custody mode
- OpenAlgo integration for natural language strategy execution
- 9-layer tool policy engine now documented
- Immersive system patterns for multi-agent safety

**Docker Deployment:**
- Gateway runs on host; agents in containers
- Official docker-compose.yml + docker-setup.sh script available
- Volume mounts: `~/.openclaw` (config/secrets), `~/openclaw/workspace` (agent files)
- ~30% overhead acceptable for isolation
- Scoped secrets injection now recommended