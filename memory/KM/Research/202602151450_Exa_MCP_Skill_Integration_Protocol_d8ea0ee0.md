---
title: "Exa MCP Skill Integration Protocol"
content_type: "Research"
domain: "OpenClaw"
certainty: "Verified"
impact: "High"
confidence_score: 10
tags: ["AI", "Automation", "Coding"]
source: "MEMORY.md"
source_file: "MEMORY.md"
date: "2026-02-15"
content_hash: "d8ea0ee034d2673c"
---

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