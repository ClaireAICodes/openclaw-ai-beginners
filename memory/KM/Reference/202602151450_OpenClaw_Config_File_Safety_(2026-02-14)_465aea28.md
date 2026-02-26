---
title: "OpenClaw Config File Safety (2026-02-14)"
content_type: "Reference"
domain: "AI Models"
certainty: "Speculative"
impact: "High"
confidence_score: 9
tags: ["AI", "Automation"]
source: "MEMORY.md"
source_file: "MEMORY.md"
date: "2026-02-15"
content_hash: "465aea288e14cf3f"
---

- **CRITICAL**: `gateway config.apply` **REPLACES** the entire configuration file. Never use it with a partial JSON object.
- **ALWAYS** use `gateway config.patch` for incremental updates (add/update single fields).
- If you must use `config.apply`, first fetch the full config with `gateway config.get`, merge your changes, then apply the complete JSON.
- **Never** reconstruct or guess the config structure - always preserve existing keys (API keys, auth profiles, model configs, skills, plugins, etc.)
- After any config modification, verify with `gateway config.get` that all expected sections are present.
- **Enshrined in AGENTS.md** under "Configuration Management" section.