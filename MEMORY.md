# MEMORY.md - Claire's Long-Term Memory

This file contains curated memories, permanent decisions, and established standards for my service to Master Phil.

## Standards & Protocols

### GitHub Documentation Standardization Protocol
Established: 2026-02-11
Description: A 4-phase process (Discovery, README Architecture, Visual Sourcing/Verification, and Deployment) to ensure every GitHub repository I build is presented with high-performance documentation and a consistent aesthetic.

Detailed steps are maintained in `AGENTS.md`.

### GitHub Collaborator Access Policy
Established: 2026-02-12
Description: All GitHub repositories created for Master Phil must include `AzureKn1ght` as a collaborator with **write** access. This ensures Master maintains full control and access regardless of which GitHub account is used to create the repository.

**Procedure:**
- Immediately after repository creation, run: `gh api -X PUT repos/<owner>/<repo>/collaborators/AzureKn1ght -f permission='push'`
- Verify by checking repository collaborators list
- Record the collaborator addition in memory logs

This policy applies to all public and private repositories created on behalf of Master Phil.

### GitHub Repository Metadata Standard
Established: 2026-02-15
Description: Every GitHub repository created for Master Phil must include three essential metadata fields for discoverability, branding, and SEO. These fields must be set immediately after repository creation, before the first push or as part of the initial setup.

**Required Metadata:**
1. **Description** (`--description`) — Concise, clear one-line summary of the repository's purpose and value
   - Example: "OpenClaw skill for local knowledge base management — sync memory files to organized folders with intelligent classification"
2. **Homepage/Website** (`--homepage`) — URL pointing to documentation, live demo, or primary resource
   - Example: "https://github.com/ClaireAICodes/openclaw-skill-knowledge-management#readme" (anchor to README section)
3. **Topics** (`--add-topic`) — Array of 5–15 relevant keywords for discoverability
   - Must include: `openclaw` (if applicable), primary domain (e.g., `ai`, `automation`, `web3`), and specific purpose (e.g., `knowledge-management`, `trading-bot`)
   - Use hyphens for multi-word topics (`local-storage`, `cost-optimization`)
   - Topics should be lowercase, no spaces

**Standard Topics Taxonomy:**
- Core platform: `openclaw` (always include for OpenClaw-related repos)
- Skill type: `skill`, `plugin`, `integration`, `template`, `starter`
- Domain: `ai`, `automation`, `crypto`, `web3`, `trading`, `productivity`, `security`, `devops`
- Function: `knowledge-management`, `cost-optimization`, `monitoring`, `backup`, `deployment`, `scraping`, `research`
- Tech stack: `nodejs`, `python`, `docker`, `github-actions`, `cli`
- Storage: `local-storage`, `cloud`, `database`, `markdown`, `notion`

**Procedure (after `gh repo create`):**
```bash
gh repo edit <owner>/<repo> \
  --description "Clear, concise one-line description" \
  --homepage "https://github.com/<owner>/<repo>#readme"

# Add topics (5–15)
gh repo edit <owner>/<repo> \
  --add-topic openclaw \
  --add-topic skill \
  --add-topic knowledge-management \
  --add-topic ai \
  --add-topic automation
```

**Verification:**
- Check: `gh api -X GET repos/<owner>/<repo> | jq '.description, .homepage, .topics'`
- Ensure description is ≤ 100 characters, homepage is valid URL, topics array has 5+ items

**Rationale:**
- GitHub search relies heavily on topics and description
- Repositories without metadata appear unprofessional and are harder to discover
- Consistent metadata improves brand recognition and ecosystem curation

**Applies to:** All public and private repositories created on behalf of Master Phil, including skills, tools, agents, and project code.

### Exa MCP Skill Integration Protocol
Established: 2026-02-12
Description: Standard protocol for integrating Exa MCP server tools into OpenClaw as a skill. Provides advanced search, crawling, and research capabilities through a unified command interface.

**Skill Details:**
- **Name:** exa-mcp
- **Location:** `/home/ubuntu/.nvm/versions/node/v24.13.0/lib/node_modules/openclaw/skills/exa-mcp/`
- **Binary:** `exa-mcp` (executable Node.js script)
- **Required Environment Variable:** `EXA_API_KEY`
- **Tools Available:** web_search_exa, web_search_advanced_exa, get_code_context_exa, crawling_exa, company_research_exa, people_search_exa, deep_researcher_start, deep_researcher_check
- **Usage:** `exa-mcp <tool_name> '<json_arguments>'`

**Implementation:**
1. Create skill directory in global node_modules
2. Implement single binary wrapper for all MCP tools
3. Define SKILL.md with metadata and usage
4. Set EXA_API_KEY environment variable to enable
5. Skill automatically available to OpenClaw agents

This protocol ensures consistent integration of external MCP servers into the OpenClaw ecosystem.

### After Action Review (AAR) Framework
Established: 2026-02-11
Description: Mandatory continuous improvement framework triggered by significant task/project completion. Immediate structured reflection with 5 questions, rating system, and dual storage (local + Notion).

Detailed framework is maintained in `AGENTS.md` and `AAR.md`.

### OpenClaw Configuration Backup Protocol
Established: 2026-02-15
Description: Robust daily backup of all OpenClaw configuration and workspace data to Google Drive using a dedicated script with deduplication, cleanup, and reliable model routing.

**Components:**
- Backup script: `/home/ubuntu/.openclaw/workspace/backup-to-gdrive.sh`
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

### AI Model Cost Optimization Strategy
Established: 2026-02-12
Description: Strategic framework for selecting and routing AI models based on task complexity, cost, and performance requirements in the 2026 landscape.

**Core Principles:**
1. **Tiered Model Routing:** Free models (MiMo, Devstral, Step-3.5 Flash) for exploration; premium (GPT-5.3, Claude Opus) for final verification
2. **Context Caching:** Enable everywhere for 75-90% savings on repeats
3. **Task Specialization:** Match model strengths (Devstral for coding, StepFlash for agentic workflows)
4. **Cost-Aware Selection:** Free models now match 2024 paid tier performance

**2026 Free Tier Leaders:**
- Xiaomi MiMo-V2-Flash (309B MoE) - coding specialist
- Devstral 2 (123B) - agentic coding with failure recovery
- Step-3.5 Flash (196B/11B) - best all-rounder
- NVIDIA Nemotron 3 Nano (30B MoE) - fully open weights

**Key Metrics:**
- Step-3.5 Flash: 100-350 tok/s, 256K context, 74.4% SWE-bench
- DeepSeek V3.2: 33 tok/s, 163K context, $0.25/$0.38 per 1M
- MiMo-V2: ~100 tok/s, 256K context, ~77% SWE-bench, free

### OpenClaw Implementation Plan
**Established:** 2026-02-12  
**Source:** 3 comprehensive research reports (24 queries, 70+ sources)

**Key Themes:**
- Security hardening (Docker, least-privilege, skill auditing) is non‑negotiable
- Multi‑agent architecture reduces token bloat by 60–80%
- Cost optimization via prompt caching, context limits, memory_search
- Browser automation as a killer differentiator
- Web3 integration accelerating (PolyClaw, LoomLay SDK)
- Passive income models diversifying (picks‑and‑shovels services, content pipelines)
- Production mindset required (audit logging, session pruning, monitoring)

**4‑Phase Plan Overview:**
- **Phase 1 (Weeks 1–2):** Foundation — multi‑agent architecture, Docker isolation, prompt caching, context limits, audit logging
- **Phase 2 (Weeks 3–4):** Web3/Trading — PolyClaw, signal aggregation, OpenAlgo, NFT liquidity proof‑of‑concept
- **Phase 3 (Weeks 5–6):** Passive Income — content pipeline prototype, affiliate tracking, analytics, security service offering
- **Phase 4 (Weeks 7–8):** Optimization — cost sprint, browser automation, monitoring, knowledge base

**Success Metrics:**
- Token reduction: 60–80% (target 70%)
- Agent reliability: 99% uptime, <1% error rate
- Polymarket arbitrage: 5+ opportunities/week
- Content output: 10+ articles/week with 1k+ views each
- Passive income: $500+/month by month 3
- Consulting clients: 2–3 at $1k+/project by month 3

**Full Report:** `Research/OpenClaw Ideas/actionable-insights-2026-02-12.md`

### Priority 1: Multi-Agent Architecture
**Impact:** Reduces token bloat by 70%, improves reliability, enables per‑agent cost tuning.

**Implementation:**
- Create 4 specialized agents: Trading, Research, Content, Admin
- Configure each with its own skill set and model routing
- Set up workspace isolation (separate `~/.openclaw/workspaces/`)

**Timeline:** Week 1–2

**Resources:**
- Multi-agent architecture: https://www.getopenclaw.ai/help/multi-agent-architecture
- Mission Control pattern: https://clawctl.com/blog/mission-control-multi-agent-squad-openclaw

### Priority 2: PolyClaw Integration
**Impact:** Automated Polymarket arbitrage with LLM‑driven event analysis.

**Implementation:**
- Deploy PolyClaw skill for market monitoring
- Build custom signal aggregator: Twitter sentiment + Dune queries + on‑chain flows
- Integrate OpenAlgo API for natural language strategy execution
- Configure risk limits: max position size, stop‑loss, daily loss cap

**Timeline:** Prototype 1–2 weeks, production 4–6 weeks

**Resources:**
- PolyClaw: https://chainstack.com/integrating-chainstack-with-openclaw-bot-for-polymarket/
- OpenAlgo: https://blog.openalgo.in/automating-trading-with-openalgo-and-openclaw-de55cc2b2d63
- Trading automation: https://openclawai.me/blog/trading-automation

### Priority 3: NFT Liquidity Feature
**Impact:** Differentiates NFT project; solves illiquidity pain point.

**Implementation:**
- Install LoomLay OpenClaw Plugin (`@loomlay/openclaw-wallet-plugin`)
- Build skill to monitor floor prices across marketplaces
- Implement instant‑sell via LoomLay liquidity pools
- Add cross‑chain inventory management

**Technical:** Plugin provides 29 native tools; self‑custody mode; works out of the box.

**Timeline:** Proof‑of‑concept in Phase 2 (Weeks 3–4)

**Resources:** https://docs.loomlay.com/sdk/openclaw-plugin

### Priority 4: Security Hardening Routine
**Prerequisite:** Must complete BEFORE any financial integration.

**Implementation Checklist:**
- [ ] Docker containerization (bind to localhost, reverse proxy with TLS)
- [ ] Firewall rules limiting outbound traffic to whitelisted APIs only
- [ ] Audit logging to file (all agent actions, tool calls, errors)
- [ ] Weekly skill audits (VirusTotal scan, code review)
- [ ] Credential rotation schedule (API keys, SSH keys)
- [ ] Egress control and network isolation
- [ ] Enable prompt caching and context limits

**Risk Mitigation:**
- Prevents data exfiltration, destructive commands, credential exposure
- Addresses "poisoned plugin" supply‑chain risks

**Timeline:** Immediate — start during Phase 1, complete within Week 2

**Resources:**
- Production security checklist: https://openclaw.academy/blog/how-to-secure-openclaw-agent-guide
- Security best practices: https://sapt.ai/insights/openclaw-architecture-security-agentic-ai-best-practices

### Priority 5: Content-to-Monetization Pipeline
**Impact:** Passive income engine; proven by multiple creators.

**Implementation:**
- Build "Moltbook agent social network" pattern:
  1. Research agents aggregate trending topics
  2. Writer agent creates outlines and drafts (YouTube transcripts → blog posts)
  3. Creator agent generates visuals and formats
  4. Publisher agent distributes (Medium, Twitter, Telegram) with affiliate link insertion
  5. Analytics agent tracks performance and feeds back to research

**Monetization:**
- Affiliate revenue (Amazon, TradingView, OpenRouter)
- Ad networks (Mediavine, AdSense after 50k sessions/month)
- Sponsored content leads
- Lead generation for consulting

**Timeline:** Prototype in Phase 3 (Weeks 5–6)

**Resources:**
- Julian Goldie's agent social network: https://www.linkedin.com/posts/juliangoldieseo_this-openclaw-moltbook-workflow-is-insane-activity-7425504007529586689-Kvsh
- Content automation use cases: https://www.forwardfuture.ai/p/what-people-are-actually-doing-with-openclaw-25-use-cases

### Priority 6: Cost Optimization Sprint
**Goal:** 70% token reduction in 30 days.

**4 Strategies:**
1. **On-demand loading** — Only load memory when needed (60% context overhead savings)
2. **Smart memory pruning** — Automatically archive old conversations (>30 days)
3. **Tool schema filtering** — Remove unused skills from agent toolset
4. **Prompt caching** — Enable on all LLM providers (75-90% savings on repeats)

**Measurement:**
- Track tokens/month and cost per agent
- Set up billing alerts
- Compare before/after metrics

**Timeline:** Sprint in Phase 4 (Week 7–8), but apply principles from Day 1

**Resources:**
- Token economics strategies: https://medium.com/@kjobear/openclaw-token-economics-strategies-9376ee8154c2
- Real-world cost reduction: https://eastondev.com/blog/en/posts/ai/20260205-openclaw-performance/

### Priority 7: Security Service Offering
**Opportunity:** Monetize your hardening expertise.

**Service Package:**
- "Production‑Grade OpenClaw Deployment" for indie hackers/SMEs ($500‑2000/setup)
- Includes: Docker container, firewall config, audit logging, credential management, monitoring
- Video course + playbook ($99‑297) based on this research

**Market Validation:**
- Superframeworks: "setup complexity" is top opportunity
- Revenue signals:个体 hackers earning $3,600/month from similar services

**Timeline:** Package in Phase 3 (Weeks 5–6), launch first client by Week 8

**Resources:**
- Business ideas analysis: https://superframeworks.com/articles/openclaw-business-ideas-indie-hackers
- Case study: Johann's $15K with OpenClaw: https://www.youtube.com/watch?v=a9BHAjRSWOo

## Lessons Learned

### Data Privacy (2026-02-11)
- **CRITICAL**: Never push internal configuration, persona, or memory files (`.agent`, `AGENTS.md`, `USER.md`, `SOUL.md`, `memory/`) to public repositories.
- Always verify the staging area before pushing to shared contexts.

### OpenClaw Config File Safety (2026-02-14)
- **CRITICAL**: `gateway config.apply` **REPLACES** the entire configuration file. Never use it with a partial JSON object.
- **ALWAYS** use `gateway config.patch` for incremental updates (add/update single fields).
- If you must use `config.apply`, first fetch the full config with `gateway config.get`, merge your changes, then apply the complete JSON.
- **Never** reconstruct or guess the config structure - always preserve existing keys (API keys, auth profiles, model configs, skills, plugins, etc.)
- After any config modification, verify with `gateway config.get` that all expected sections are present.
- **Enshrined in AGENTS.md** under "Configuration Management" section.

### Model Selection Intelligence (2026-02-12)
The free tier ecosystem in 2026 is production-capable; don't default to paid models without cost-benefit analysis. Step-3.5 Flash's 11B active tokens out of 196B total demonstrates MoE efficiency can match frontier performance at 5-19x lower cost. Multi-model routing is essential for agentic workflows that can consume 500K+ tokens per task. Always check OpenRouter's current rate limits for free tiers (as of July 2025: "low daily request limits unsuitable for production").


---
