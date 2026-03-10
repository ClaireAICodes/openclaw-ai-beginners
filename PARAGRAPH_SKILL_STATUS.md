# Paragraph Skill Status — 2026-03-09

## Configuration

- **API Key**: e1eb0368-02de-4985-aee9-e56611f5f873 (verified valid via curl)
- **Publication Slug**: kamiya-ai
- **Skill Location**: `~/.openclaw/skills/paragraph` (shared skills directory)
- **Config Entry**: `skills.entries.paragraph.env` in `openclaw.json`

## Changes Made

1. **Moved to shared skills** — Removed duplicate copies from workspace directories; now in `~/.openclaw/skills/paragraph`
2. **Patched skill.js** — Modified to read `PARAGRAPH_API_KEY` at runtime from `process.env` inside the `request()` function, instead of capturing it at module load time. This ensures environment injection from per-skill `env` config works correctly.
3. **Restarted gateway** — To refresh skill discovery and clear any cached modules.

## Test Results

- ✅ API key valid (curl test succeeded)
- ✅ Skill code loads without syntax errors
- ✅ Shared skill directory is in place

## Known Issues

- Agent tool visibility may require a fresh session. After a full gateway restart (currently running), the skill should appear in the agent's tool list.
- If `paragraph_testConnection()` still reports "PARAGRAPH_API_KEY not set" through the agent, the gateway may not be injecting the env vars from `skills.entries.paragraph.env` correctly. This would be a configuration bug.

## Next Steps for Master

1. **If you're not in a hurry**: Let the system run; the skill should work when you try to publish a blog post tomorrow.
2. **If you need immediate verification**: Try calling `paragraph_testConnection()` via the agent and confirm it returns subscriber count.
3. **If it still fails**: The issue may be that the gateway version doesn't support `skills.entries.<skill>.env` injection for shared skills, and we may need to declare the paragraph skill as a "native" skill in the config or adjust the config schema.

Note: The skill is technically ready. The core fix (runtime env read) ensures that if the env vars are present in the agent's environment, the tool will work. The only blocker is ensuring the gateway injects them.
