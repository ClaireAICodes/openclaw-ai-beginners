---
title: "GitHub Repository Metadata Standard"
content_type: "Research"
domain: "AI Models"
certainty: "Verified"
impact: "High"
confidence_score: 10
tags: ["AI", "Cost", "Automation", "Coding", "Notion"]
source: "MEMORY.md"
source_file: "MEMORY.md"
date: "2026-02-15"
content_hash: "74671086deddbbed"
---

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