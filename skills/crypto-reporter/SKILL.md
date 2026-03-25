# Crypto Reporter Skill

A comprehensive OpenClaw skill for generating daily cryptocurrency analysis reports with fundamentals, technicals, sentiment, risk assessment, and clear trading verdicts.

## Overview

This skill automates the research and compilation of detailed daily crypto market reports. It aggregates data from multiple sources, performs multi-dimensional analysis, and produces actionable intelligence with Buy/Hold/Sell recommendations.

**Key Features:**
- Multi-source data aggregation (news, on-chain metrics, social sentiment)
- Comprehensive analysis across 4 dimensions: Fundamentals, Technicals, Sentiment, Risks
- Weighted scoring algorithm for final verdict
- Support for multiple output formats (Markdown, JSON)
- Configurable tracked assets and analysis parameters
- Cron-integrated for daily automated execution

## Usage

### As a Cron Job

The skill can be scheduled to run daily via OpenClaw's cron system:

```yaml
# Add to OpenClaw cron config
- name: Daily Crypto Report
  schedule:
    kind: cron
    expr: "0 6 * * *"  # 6 AM UTC daily
  payload:
    kind: agentTurn
    message: "Generate daily cryptocurrency summary report"
    model: openrouter/stepfun/step-3.5-flash:free
  sessionTarget: isolated
  delivery:
    mode: announce
```

### Manual Invocation

You can also trigger the report manually by sending a message to the agent:

```
Generate comprehensive crypto report for today
```

Or for a specific date:

```
Generate crypto report for 2026-02-26
```

## Report Structure

The generated report includes:

1. **Executive Summary** - Key highlights and overall verdict
2. **Market Overview** - Market cap, volume, BTC dominance, Fear & Greed index
3. **Fundamentals Analysis**
   - Network metrics (active addresses, transactions)
   - On-chain activity (exchange flows, whale movements)
   - Development activity
   - Adoption indicators
4. **Technical Analysis**
   - Price action and momentum indicators (RSI, MACD)
   - Support and resistance levels
   - Moving averages
   - Volume analysis
5. **Sentiment Analysis**
   - Social media sentiment scores
   - News tone analysis
   - Institutional flow data
   - Derivatives metrics (funding rates)
6. **Risk Assessment**
   - Regulatory risk level and concerns
   - Technical vulnerabilities
   - Market structure risks
   - Liquidity risks
   - Systemic risk score
7. **Trading Verdict**
   - Overall recommendation (Strong Buy / Buy / Hold / Sell / Strong Sell)
   - Confidence score (0-10 scale)
   - Score breakdown by category
   - Risk/reward ratio
   - Time horizon
8. **Watchlist** - Assets requiring close monitoring
9. **Methodology Notes** - Explanation of analysis approach

## Configuration

The skill uses a configuration file at `/home/node/.openclaw/workspace/crypto-report/config.yaml`.

### Key Configuration Options

```yaml
# Assets to track (by ticker symbol)
TRACKED_ASSETS:
  - BTC
  - ETH
  - ADA
  - SOL

# Data sources to query
DATA_SOURCES:
  - name: "news"
    queries:
      - "cryptocurrency market analysis today"
      - "bitcoin technical analysis"
  - name: "institutional"
    queries:
      - "institutional crypto adoption"
      - "bitcoin ETF flows"

# Verdict weights (must sum to 1.0)
VERDICT_WEIGHTS:
  fundamentals: 0.30
  technicals: 0.25
  sentiment: 0.20
  risks: 0.25

# Output settings
OUTPUT_DIR: "/home/node/.openclaw/workspace/memory/crypto-reports"
REPORT_FORMAT: "markdown"  # or "json" / "both"
```

## Data Sources

The skill queries multiple source categories:

1. **News & Analysis** - Latest market commentary and analysis articles
2. **Institutional** - ETF flows, institutional adoption, regulatory updates
3. **Technical** - Chart analysis, indicator readings, on-chain metrics
4. **Sentiment** - Social media sentiment, fear & greed index, Google trends
5. **Risks** - Regulatory enforcement, security incidents, market risks

Each source type has configurable queries to target specific information needs.

## Output

Reports are saved to the configured output directory (default: `memory/crypto-reports/`) with filenames:

```
crypto-report-2026-02-26.md
crypto-report-2026-02-26.json
crypto-report-latest.md (symlink)
```

Additionally, if notifications are enabled, a summary is sent via the configured messaging channel.

## Integration with OpenClaw

This skill leverages OpenClaw's built-in capabilities:

- **web_search** - Aggregating news and analysis from multiple sources
- **memory** - Storing reports and maintaining version history
- **message** - Sending notifications and summary alerts
- **cron** - Automated daily execution

The skill is designed to be cost-effective, using free-tier models where possible and optimizing token usage through query limits and response caching.

## Future Enhancements

Planned features:
- Integration with on-chain APIs (Glassnode, Santiment, CryptoQuant)
- Historical backtesting of verdict accuracy
- Portfolio impact analysis
- Customizable risk tolerance profiles
- Multi-language support
- Telegram/Discord bot integration

## Troubleshooting

**Issue:** Report generation fails with quota errors
**Solution:** Check that you have sufficient API quota on your configured model. Consider using a different model or reducing `MAX_NEWS_ARTICLES`.

**Issue:** Missing data for certain assets
**Solution:** The skill depends on publicly available information. Some altcoins may have less coverage. Adjust `TRACKED_ASSETS` to focus on major cryptocurrencies with sufficient data sources.

**Issue:** Reports take too long to generate
**Solution:** Reduce `MAX_NEWS_ARTICLES` and `MAX_ANALYSIS_PIECES` in config, or reduce the number of tracked assets.

## Support

For issues or feature requests, open an issue on the skill's repository or contact your OpenClaw administrator.
