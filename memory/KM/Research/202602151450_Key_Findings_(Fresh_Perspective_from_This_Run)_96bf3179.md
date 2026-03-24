---
title: "Key Findings (Fresh Perspective from This Run)"
content_type: "Research"
domain: "AI Models"
certainty: "Verified"
impact: "High"
confidence_score: 9
tags: ["AI", "Benchmark", "Cost", "Automation"]
source: "daily"
source_file: "2026-02-13.md"
date: "2026-02-13"
content_hash: "96bf31791b037db4"
---

**Security Deep Dive:**
- Official guides: "How to Secure Your OpenClaw Agent" (OpenClaw Academy) emphasizes DM pairing, Docker, least-privilege
- Hostinger: "Keep OpenClaw private by default, isolated execution, permission controls"
- Sapt.ai: Architecture deep dive on prompt injection & privilege escalation risks
- Jamf Threat Labs: Insider threat analysis; warns about data exfiltration and destructive commands
- **Action:** Must implement all security standards BEFORE any financial integration

**Skills Ecosystem Maturity:**
- 700+ skills via ClawHub; 50+ tagged "productivity"; most are broken experiments
- Official integrations list: weather-reporter, flight-tracker, github-manager, smart-home-controller, news
- ezBookkeeping integration shows vertical skill bundling potential
- Skill building guide available; SKILL.md format standardized

**Performance Optimization Specifics:**
- EastonDev: 80% cost cut via context reduction, tiered routing, prompt caching
- 99x speedup video: M3 Ultra Mac Studio with 512GB RAM
- APIYI: 6 reasons for token drain + money-saving guide
- InsiderLLM: 97% reduction via Ollama heartbeats, tiered routing, session reset culture
- **Config examples found:** `num_ctx: 2048`, `n_gpu_layers: 35` for speed

**Workflow Patterns Catalog:**
- Dev Shorts: Practical workflows from author's daily use; isolation importance
- Skywork: 12 practical use cases (client onboarding, data transformation, scheduling)
- Robo Rhythms: Beginner to advanced progression guide
- Oh My OpenClaw: Excel reporting pipelines (chaos → clean dashboard)
- Browser Automation: 3 modes (hosted/managed, sandbox, user profile); headless 24/7 operation

**Passive Income Models:**
- Medium article "33 automations" (Phil Rentier) — echoes our thesis
- Superframeworks: 5 business ideas with revenue data; picks-and-shovels focus
- YouTube: How to make money "halal" ways; security warnings
- Leveling Up with Eric Siu: Real business use cases (SEO, product, sales)
- Investment analyst agent: Automated research, modeling, monitoring
- Marketing 24/7: Brand monitoring, competitor tracking, content repurposing

**PolyClaw Deep Dive:**
- Official site: `polyclaw.ai` — autonomous agents, $POLYCLAW token
- Stats: $847K+ volume 24h, 127+ agents, 68% win rate, $32K+ buybacks
- Clanker token link: verified token on Base
- Playbooks skill registry:
  - `polymarket-analysis`: cost arbitrage, whale tracking, sentiment, momentum
  - `polymarket-assistant`: cross-platform (Polymarket + Hyperliquid) with hedging
  - `polymarket-trader`: trending, crypto, politics, sports queries
  - `polymarket`: basic Gamma API querying
- YouTube: Arbitrage strategies (rebalance, combinatorial) — research paper analysis
- Phemex News: Clawdbot spotted mispricing
- **Gap:** No skills focused on portfolio-level risk management; this is our opportunity

**NFT Liquidity Context:**
- Blocmates: "How not to go broke using OpenClaw" — risk management focus
- CoinMarketCap: Lists PolyClaw, autonomous researcher/trader, airdrop farming, on-chain sentry as crypto use cases
- LoomLay plugin mentioned: 29 tools, self-custody mode, instant liquidity
- Security breach: Hackers poisoned plugin marketplace with malicious skills (Feb 9)
- **Action:** Must audit any plugin before use; prefer official sources

**Productivity Hacks & Mission Control:**
- Julian Goldie (LinkedIn): "Moltbook agent social network" — agents talk to each other, generate content ideas from discussions
- Clawctl Blog: Mission Control — 10 agents, one lead; tasks created, claimed, executed, reviewed
- Jonathan Tsai: "OpenClaw Command Center" — production-grade multi-agent orchestration
- Joerg Peetz: "How to Set Up OpenClaw But the Right Way" — 23 min guide; emphasizes not another chatbot
- Oh My OpenClaw: Best productivity skills — tested 50+, only 10 delivered consistently
- Skywork: Multi-step workflows guide; planner-executor pattern; heartbeats vs cron distinction
- Molt Founders Runbook: **"Treat OpenClaw as infrastructure, not a chatbot"** — key mantra
- Best Practices: Memory strategies, automation patterns, cost optimization, debugging

**Additional Critical Insights:**

- **Substack vs Medium:** Medium's official API dead; only reverse-engineered GraphQL (fragile). Substack has official OAuth API (draft/publish, image upload). **Recommendation: Build Substack publisher skill, ignore Medium automation.**

- **Exa MCP Integration:** Successfully used after binary path discovery. Tool provides `web_search_exa`, `deep_researcher_start`, `crawling_exa`, `company_research_exa`, `people_search_exa`. Very powerful for research automation. **Should be integrated as a skill.**

- **Skill Quality Crisis:** Many skills are "half-finished experiments" with missing configs, stack traces. **Opportunity:** Build a skill validator/curator that rates skills on completeness, security, maintenance status.

- **Real People Making Money:** Signals are concrete: $3,600/mo first month, $15K+ in weeks, 5-figure deals by day 5. Not hype — verified by multiple sources.