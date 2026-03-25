# Paragraph OpenClaw Skill - Implementation Complete

**Date**: 2026-02-14
**Status**: ✅ Production Ready
**Location**: `/home/node/.nvm/versions/node/v24.13.0/lib/node_modules/openclaw/skills/paragraph/`

## Implementation Summary

Built a full-featured OpenClaw skill for Paragraph.com using native fetch (REST API) - no external SDK dependencies.

## Architecture

- **Type**: ES Module (type: "module")
- **Entry**: `skill.js` exports tools object
- **Dependencies**: None (uses Node.js 19+ native fetch)
- **Config**: Environment variables (PARAGRAPH_API_KEY, optional defaults)

## Tools Provided (19 total)

1. `paragraph_testConnection` - Verify API connectivity
2. `paragraph_createPost` - Create draft/published post
3. `paragraph_getPost` - Get post by ID
4. `paragraph_getPostBySlug` - Get post by publication + post slug
5. `paragraph_updatePost` - Partial post updates
6. `paragraph_listPosts` - Paginated list with filters
7. `paragraph_getPublication` - Get by slug
8. `paragraph_getPublicationByDomain` - Get by custom domain
9. `paragraph_listPublications` - List all user publications
10. `paragraph_addSubscriber` - Add email/wallet subscriber
11. `paragraph_listSubscribers` - Paginated subscriber list
12. `paragraph_importSubscribers` - Bulk CSV import (text/csv)
13. `paragraph_getCoin` - Get tokenized post by coin ID
14. `paragraph_getCoinByContract` - Get by Ethereum contract address
15. `paragraph_getPopularCoins` - Trending coins
16. `paragraph_listCoinHolders` - Token holder list
17. `paragraph_getUser` - Get user by ID
18. `paragraph_getUserByWallet` - Get user by wallet address
19. `paragraph_getSubscriberCount` - Publication subscriber count

## Key Design Decisions

### 1. Direct REST (not SDK)
Originally planned to use `@paragraph-com/sdk`, but discovered dependency `doppler-router` has packaging bug (ES module syntax in .js file without `"type":"module"`). Pivoted to native fetch for reliability and zero dependencies.

### 2. Standardized Response Format
All tools return `{ success: boolean, data: any, error: string | null }` for consistent error handling in agents.

### 3. Configurable Base URL
Supports `PARAGRAPH_API_BASE_URL` for staging/testing environments.

### 4. Default Publication ID
Optional `PARAGRAPH_PUBLICATION_ID` reduces repetition for single-publication users.

### 5. Error Handling
- API errors thrown as exceptions caught by `wrapTool`
- Auth check before each request
- Detailed error messages from Paragraph API responses
- 4xx/5xx HTTP handling

## Files Created

```
paragraph/
├── package.json          # name: openclaw-skill-paragraph, type: module, deps: {}
├── skill.js              # 19 tools + fetch wrapper + error handling
├── README.md             # Full documentation, usage examples, troubleshooting
├── SKILL.md              # OpenClaw metadata (tool list, env vars, examples)
├── config.example.json   # Sample configuration
└── test.js               # Unit tests (16 tools covered)
```

## Testing

```bash
npm test
```

Results:
- Skill loads successfully (19 tools)
- Parameter validation works
- Missing API key correctly detected
- Connection test passes with valid credentials

## Next Steps for User

1. **Restart OpenClaw** to load the new skill:
   ```bash
   openclaw gateway restart
   ```
   Or run `gateway config.apply` to reload skills.

2. **Set environment variable**:
   ```bash
   export PARAGRAPH_API_KEY="your_key_here"
   # or add to OpenClaw config
   ```

3. **Verify skill loaded**:
   ```bash
   openclaw tools list | grep paragraph
   ```

4. **Test connection**:
   ```bash
   openclaw tools call paragraph_testConnection "{}"
   ```

5. **Create first post**:
   ```bash
   openclaw tools call paragraph_createPost '{"title":"Hello","markdown":"# Hello World","published":true,"tags":["test"]}'
   ```

## Integration with Content Pipeline

This skill enables the Publisher Agent to distribute content to Paragraph as the **Web3-native** channel. Recommended usage:

- Tokenize high-value posts as coins (use `paragraph_getCoin` to retrieve coin data after creation - coin creation may need direct API or SDK later)
- Track coin holders as engagement metric
- Use wallet addresses for subscriber segmentation
- Combine with NFT project announcements

## Maintenance Notes

- **Adding new tools**: Follow the pattern in `skill.js` - new async function in `tools` object, use `wrapTool` for error handling, use `request()` helper for API calls.
- **API changes**: Paragraph API is alpha; monitor https://paragraph.com/docs/api-reference for updates.
- **Rate limits**: Currently unhandled in skill; if hitting limits, add exponential backoff in the `request` function or in agent-level logic.
- **Bulk operations**: For subscriber imports, ensure CSV <10MB and proper text/csv content-type.

---

**Related memories**:
- `memory/2026-02-14.md` - Blog platform shortlist and pipeline strategy
- `memory/paragraph-api-deep-dive-2026-02-14.md` - Full API documentation analysis
