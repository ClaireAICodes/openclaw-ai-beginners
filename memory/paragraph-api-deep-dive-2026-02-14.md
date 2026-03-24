# Paragraph API Deep Dive - Full Documentation Analysis

**Date**: 2026-02-14
**Source**: https://paragraph.com/docs/llms-full.txt
**Status**: Alpha API (breaking changes possible)

---

## API OVERVIEW

Paragraph provides a REST API + TypeScript SDK for onchain publishing. Base URL: `https://api.paragraph.com/v1`

**Authentication**: API key in Authorization header
**Rate Limiting**: Yes (contact support for increases)
**SDK**: `@paragraph-com/sdk` (TypeScript, full type safety)

---

## CORE ENDPOINTS

### 1. POSTS

#### Create Post
```
POST /v1/posts
Authorization: Bearer {API_KEY}
Content-Type: application/json

{
  "title": "string (required)",
  "markdown": "string (required) - converted to TipTap JSON",
  "published": true (default),
  "sendNewsletter": false,
  "tags": ["string"],
  "coverImage": "URL",
  "customDomain": "string",
  "series": "string",
  "canonicalUrl": "string",
  "coinData": { ... } // optional tokenization
}
```

**Behavior**: Published by default. Newsletter sent if `sendNewsletter: true`.

#### Get Post
```
GET /v1/posts/{postId}
GET /v1/publications/{publicationId}/posts/slug/{postSlug}
GET /v1/publications/slug/{publicationSlug}/posts/slug/{postSlug}
```

#### List Posts
```
GET /v1/posts/feed (curated)
GET /v1/posts/tag/{tag} (by tag, newest first)
GET /v1/publications/{publicationId}/posts (paginated)
```

---

### 2. PUBLICATIONS

```
GET /v1/publications/{publicationId}
GET /v1/publications/slug/{slug}
GET /v1/publications/domain/{domain} (custom domain)
GET /v1/publications/{publicationId}/subscribers/count
```

Publication object:
```json
{
  "id": "string",
  "name": "string",
  "slug": "string",
  "ownerUserId": "string",
  "customDomain": "string|null",
  "summary": "string",
  "logoUrl": "string|null"
}
```

---

### 3. SUBSCRIBERS

#### Add Subscriber
```
POST /v1/subscribers
{
  "email": "string (optional)",
  "wallet": "string (optional)",
  "sendWelcomeEmail": true
}
```
At least one of email or wallet required. No duplicates.

#### List Subscribers
```
GET /v1/subscribers (paginated, newest first, active only)
```

#### Import CSV
```
POST /v1/subscribers/import
Content-Type: text/csv
```
CSV columns: `email`/`subscriberEmail`, `wallet_address`, `created_at` (optional). Max 10MB.

---

### 4. COINS (Tokenized Posts)

Paragraph integrates tokenization via Doppler. Each coin represents a tokenized post.

#### Get Coin
```
GET /v1/coins/{id}
GET /v1/coins/contract/{contractAddress}
```

#### Get Quote
```
GET /v1/coins/quote/{id}
GET /v1/coins/quote/contract/{contractAddress}
```
Returns ETH exchange rate.

#### Buy/Sell Args
```
GET /v1/coins/buy/{id}
GET /v1/coins/buy/contract/{contractAddress}
GET /v1/coins/sell/{id}
GET /v1/coins/sell/contract/{contractAddress}
```
Returns arguments needed for wallet transaction.

#### List Holders
```
GET /v1/coins/{id}/holders
GET /v1/coins/contract/{contractAddress}/holders
```
Paginated list of coin holders.

#### Popular Coins
```
GET /v1/coins/list/popular
```

---

### 5. USERS

```
GET /v1/users/{userId}
GET /v1/users/wallet/{walletAddress}
```
Returns user profile with wallet addresses, Farcaster handles.

---

## KEY FEATURES FOR AUTOMATION

### Data Format
- Posts: Markdown input, converted internally to TipTap JSON
- All responses: JSON
- Pagination: Standard cursor-based (page/limit)

### Onchain Integration
- Posts can be tokenized as "coins" via Doppler v3/v4
- Wallet-based authentication & subscriber tracking
- Arweave storage (content permanence)
- ETH gas fees apply for coin minting/trading

### SDK Benefits
- TypeScript-first, full type definitions
- Handles authentication, request formatting
- Wraps all REST endpoints
- Coming soon: onchain event listening helpers

---

## MCP SERVER INTEGRATION

Paragraph provides an MCP (Model Context Protocol) server for LLM integration:

```bash
claude mcp add --transport http paragraph https://paragraph.mintlify.app/mcp
```

Once configured, Claude Code can:
- Search Paragraph documentation
- Make API calls with authentication
- Generate code with up-to-date API knowledge
- Access real-time API information

---

## ONCHAIN EVENTS (Doppler v3 → v4)

Paragraph coins deploy via Doppler. To track them programmatically:

1. Subscribe to `Airlock.Create` events on Base
2. Verify it's a Paragraph coin: `Airlock.getAssetData(asset)`
3. Follow price-discovery surface:
   - v3: Uniswap v3/v2 pools
   - v4: Doppler Hook

SDK will soon provide helpers for this.

---

## INTEGRATION CONSIDERATIONS

### Pros
- Web3-native: wallet auth, tokenization, onchain storage
- Built-in monetization via coins (token splits, trading)
- SDK simplifies integration
- MCP server for AI-assisted development
- Growing ecosystem (Paragraph, Mirror, Doppler)

### Cons
- Alpha API: breaking changes likely
- Rate limited (may need to request increases)
- Gas fees for onchain operations
- Smaller audience than dev.to/Medium
- Documentation still evolving

---

## STRATEGIC FIT FOR MASTER PHIL

Paragraph aligns perfectly with:
1. **NFT project** - tokenized posts, coin mechanics, NFT community
2. **Web3 content strategy** - reaches crypto-native audience
3. **Monetization innovation** - coins enable community ownership, trading fees
4. **Technical credibility** - cutting-edge onchain publishing

### Use Cases
- NFT project announcements (tokenized posts = immediate community stake)
- Educational content about Web3 (earn tips in coins)
- Paid newsletters (coin-gated access)
- Live project updates (onchain timestamped)

---

## IMPLEMENTATION PRIORITY: HIGH

Should be one of first 3 platforms in Publisher Agent (alongside Ghost + dev.to).

**Required Setup**:
1. Create Paragraph account
2. Generate API key (Account Settings → Integrations)
3. Choose publication or create new
4. (Optional) Connect wallet for onchain features

**Publisher Agent Adapter Needs**:
- Markdown → TipTap JSON conversion (handled by Paragraph)
- Coin metadata handling (if tokenizing posts)
- Wallet transaction support (for buy/sell args)
- Onchain event tracking for coin performance

---

## RESOURCES
- API Reference: https://paragraph.com/docs/api-reference
- SDK GitHub: https://github.com/paragraph-xyz/paragraph-sdk-js
- OpenAPI Spec: https://github.com/paragraph-xyz/paragraph-sdk-js/blob/main/openapi.json
- MCP Server: https://paragraph.mintlify.app/mcp
- Doppler Docs: https://docs.doppler.lol
- Community/support: support@paragraph.com

---

**Next**: Build ParagraphAdapter class in Publisher Agent using SDK wrapper.
