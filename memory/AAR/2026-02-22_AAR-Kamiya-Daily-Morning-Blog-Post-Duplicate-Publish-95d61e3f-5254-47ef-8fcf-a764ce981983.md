---
title: "Kamiya Daily Morning Blog Post - Duplicate Publication"
date: 2026-02-22
task_id: "95d61e3f-5254-47ef-8fcf-a764ce981983"
agent: "kamiya"
status: "failed"
score: 1
---

## After-Action Review

**Intended:** Write and publish a daily blog post to Paragraph.com based on latest OpenClaw research insights, with proper metadata, cover image, and a single publication.

**What happened:** The same article "The Quiet Revolution: How Vertical AI Agents Are Reshaping Work" was published THREE times. All duplicates appear in the RSS feed: https://api.paragraph.com/blogs/rss/@kamiya-ai. This indicates the script lacks idempotency checks—it creates a new post each run without verifying whether today's post already exists.

**What went well:** The content quality and image selection appear fine; the article itself is good. The automated pipeline from research insights to blog post is working in terms of content generation.

**What didn't:** No guard against duplicate publishing. The script likely uses `paragraph_createPost` every time without checking for an existing post with the same title/slug/date. Once a post is created, subsequent runs should either skip or update the existing post, not create new ones. Additionally, the URL format may need consistency: should be `https://paragraph.com/@kamiya-ai/{slug-or-id}`.

**Improvement:** Implement pre-publish uniqueness check:
1. Before calling `paragraph_createPost`, query existing posts (via Paragraph API or RSS) to see if a post with today's date or the exact title already exists.
2. If found, either skip publishing (if same content) or update the existing post using the post ID.
3. Store the published post ID/slug in a local marker file (e.g., `blog-post-2026-02-22.published`) to track what was published on which date, avoiding re-runs on the same day if the cron fires multiple times.
4. Add error handling: if `paragraph_createPost` fails due to duplicate, catch and mark as already published.

**Action taken:** Instructed Kamiya agent to write its own AAR and patch the script immediately. Will monitor next run. Also noted correct URL format for future links.
