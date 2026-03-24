---
title: "GitHub Collaborator Access Policy"
content_type: "Reference"
domain: "Process"
certainty: "Verified"
impact: "High"
confidence_score: 9
tags: ["AI", "Automation"]
source: "MEMORY.md"
source_file: "MEMORY.md"
date: "2026-02-15"
content_hash: "a70f85d63fa7f842"
---

Established: 2026-02-12
Description: All GitHub repositories created for Master Phil must include `AzureKn1ght` as a collaborator with **write** access. This ensures Master maintains full control and access regardless of which GitHub account is used to create the repository.

**Procedure:**
- Immediately after repository creation, run: `gh api -X PUT repos/<owner>/<repo>/collaborators/AzureKn1ght -f permission='push'`
- Verify by checking repository collaborators list
- Record the collaborator addition in memory logs

This policy applies to all public and private repositories created on behalf of Master Phil.