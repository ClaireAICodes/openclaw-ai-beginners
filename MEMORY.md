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

## Autonomous Ideation & Execution System (2026-03-08)

### Overview
Established: 2026-03-08
Description: A three-component autonomous system that generates improvement ideas, creates prioritized daily plans, and implements them with minimal human involvement.

**Components:**
1. **Heartbeat Ideation** (`scripts/ideate.js`) - Runs every 30 minutes (7 AM - 10 PM), generates 3-5 improvement ideas based on USER.md understanding and recent activity, stores in `ideas/YYYY-MM-DD.md`
2. **Morning Plan Generator** (`scripts/morning-plan.js`) - Runs at 6:30 AM daily, reads yesterday's ideas, prioritizes them into a plan with risk zones (Green/Yellow/Red) and specific implementation tasks, outputs to `plan/YYYY-MM-DD_plan.md`
3. **Weekly Meta-Review** (`scripts/weekly-review.js`) - Runs at 7:00 AM Sundays, analyzes execution patterns from `execution-log.md` and generates recommendations to improve ideation strategy

**Risk Stratification:**
- **Green** (autonomous execute): Low-risk items (research, documentation, internal scripts) - I implement immediately upon Master's "yes"
- **Yellow** (inform after): Medium-risk items (new repos, skill installs, API connections) - I implement and report results
- **Red** (explicit approval): High-risk items (financial, external communications, sensitive data) - I ask for approval per task even after "yes"

**User Interaction:**
- Master receives morning plan each day
- Simple response: "yes" triggers implementation of all Green + Yellow tasks
- Optional refinement: "yes green only", "yes green yellow"
- Zero involvement needed for actual execution beyond initial approval

**Tracking:**
- All ideas logged in `ideas/YYYY-MM-DD.md`
- All plans logged in `plan/YYYY-MM-DD_plan.md`
- Execution status tracked in `execution-log.md`
- Learning log enables continuous improvement of ideation quality

**Installation:**
- Cron jobs installed via `scripts/setup-cron.js`
- Heartbeat: `0,30 7-22 * * * node /home/ubuntu/.openclaw/workspace/scripts/ideate.js`
- Morning: `30 6 * * * node /home/ubuntu/.openclaw/workspace/scripts/morning-plan.js`
- Weekly: `0 7 * * 0 node /home/ubuntu/.openclaw/workspace/scripts/weekly-review.js`

**First Ideation:** 2026-03-08 - Generated 5 ideas (email triage, calendar parser, NFT monitor, trading signals, side-hustle scout)

---
