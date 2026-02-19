---
title: "Technical Notes"
content_type: "Pattern"
domain: "OpenClaw"
certainty: "Verified"
impact: "High"
confidence_score: 7
tags: ["AI"]
source: "daily"
source_file: "2026-02-14.md"
date: "2026-02-14"
content_hash: "e98a3cceb13f9156"
---

- Paragraph skill configuration verified: `PARAGRAPH_API_KEY` set
- `waitForProcessing: true` used to ensure slug/url availability (onchain processing ~25s)
- Publication: The ZAO Newsletter (`@thezao`, numeric ID 359)
- URL pattern confirmed: `https://paragraph.com/@<publication-slug>/<post-slug>`
- Both posts verified live (HTTP 200)