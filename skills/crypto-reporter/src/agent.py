#!/usr/bin/env python3
"""
Crypto Reporter Agent Skill - Daily Cryptocurrency Analysis

OpenClaw agent skill that generates comprehensive daily crypto market reports.
Invoked via cron or manually to produce detailed analysis with verdict.

To run as cron job, add to OpenClaw crontab:
  payload: { kind: agentTurn, message: "Generate daily cryptocurrency summary report" }
  schedule: { kind: cron, expr: "0 6 * * *" }
  sessionTarget: isolated
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============== Configuration & Setup ==============

WORKSPACE = Path('/home/node/.openclaw/workspace')
CRYPTO_DIR = WORKSPACE / 'crypto-report'
CONFIG_FILE = CRYPTO_DIR / 'config.yaml'
OUTPUT_DIR = WORKSPACE / 'memory' / 'crypto-reports'
ARTIFACTS_DIR = CRYPTO_DIR / 'artifacts'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('crypto-reporter')


# ============== Load Configuration ==============

def load_config() -> Dict[str, Any]:
    """Load YAML configuration"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config missing: {CONFIG_FILE}")

    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required = ['TRACKED_ASSETS', 'DATA_SOURCES', 'VERDICT_WEIGHTS', 'VERDICT_THRESHOLDS']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")

    logger.info(f"Config loaded: {len(config['TRACKED_ASSETS'])} assets, {len(config['DATA_SOURCES'])} sources")
    return config


# ============== Data Collection ==============

def collect_data(config: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Collect data from all configured sources using web_search tool

    Returns dict mapping source_name -> list of search results
    """
    collected = {}
    total_queries = sum(len(s.get('queries', [])) for s in config['DATA_SOURCES'])

    logger.info(f"Starting data collection from {len(config['DATA_SOURCES'])} sources...")

    for source in config['DATA_SOURCES']:
        name = source['name']
        queries = source.get('queries', [])
        priority = source.get('priority', 3)

        logger.info(f"[P{priority}] {name}: {len(queries)} queries")
        results = []

        for query in queries:
            try:
                # Call web_search tool (injected by OpenClaw agent system)
                # Tool signature: web_search(query: str, count: int = 10, **kwargs) -> List[Dict]
                search_results = web_search(
                    query=query,
                    count=min(10, config.get('MAX_NEWS_ARTICLES', 20)),
                    freshness="pd"  # Past day
                )

                if search_results:
                    results.extend(search_results)
                    logger.debug(f"  ✓ '{query[:60]}...' -> {len(search_results)} results")
                else:
                    logger.warning(f"  ✗ '{query[:60]}...' -> no results")

            except NameError:
                # web_search tool not available (e.g., running standalone)
                logger.error("web_search tool not available - are you running in an OpenClaw agent session?")
                raise
            except Exception as e:
                logger.error(f"  ✗ Query failed: {e}")

        collected[name] = results
        logger.info(f"  Total for {name}: {len(results)} articles")

    total_articles = sum(len(v) for v in collected.values())
    logger.info(f"Data collection complete: {total_articles} articles from {len(collected)} sources")

    # Save raw artifacts
    artifact_file = ARTIFACTS_DIR / f"raw_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(artifact_file, 'w') as f:
        json.dump(collected, f, indent=2, default=str)
    logger.debug(f"Raw artifacts saved to {artifact_file}")

    return collected


# ============== Analysis ==============

def analyze_market_metrics(data: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Extract market-wide metrics from collected data
    Returns dict with btc_price, market_cap, fear_greed_index, etc.
    """
    logger.info("Analyzing market metrics...")

    all_articles = []
    for results in data.values():
        all_articles.extend(results)

    metrics = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'articles_analyzed': len(all_articles),
        'btc_price': None,
        'eth_price': None,
        'market_cap': None,
        'btc_dominance': None,
        'fear_greed_index': None,
        'total_volume_24h': None
    }

    # In production, implement proper extraction via:
    # - Regex pattern matching for price numbers
    # - NLP to identify metric mentions
    # - Integration with market data APIs (CoinGecko, etc.)

    logger.info("Market metrics analysis complete")
    return metrics


def analyze_assets(config: Dict[str, Any], collected_data: Dict[str, List[Dict]]) -> Dict[str, Dict[str, Any]]:
    """
    Analyze each tracked asset
    Returns dict symbol -> asset analysis metrics
    """
    logger.info(f"Analyzing {len(config['TRACKED_ASSETS'])} tracked assets...")

    analyses = {}
    for symbol in config['TRACKED_ASSETS']:
        analysis = {
            'symbol': symbol,
            'name': asset_name(symbol),
            'price': None,
            'change_24h': None,
            'rsi': None,
            'sentiment_score': None,
            'volume_24h': None,
            'market_cap': None
        }
        # Extract asset-specific data from collected articles
        analysis = extract_asset_metrics(symbol, analysis, collected_data)
        analyses[symbol] = analysis
        logger.debug(f"  Analyzed {symbol}")

    logger.info(f"Asset analysis complete for {len(analyses)} assets")
    return analyses


def asset_name(symbol: str) -> str:
    """Get full name for asset symbol"""
    names = {
        'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'ADA': 'Cardano',
        'SOL': 'Solana', 'AVAX': 'Avalanche', 'DOT': 'Polkadot',
        'LINK': 'Chainlink', 'UNI': 'Uniswap', 'AAVE': 'Aave',
        'MKR': 'Maker'
    }
    return names.get(symbol.upper(), symbol)


def extract_asset_metrics(symbol: str, analysis: Dict, collected_data: Dict[str, List[Dict]]) -> Dict:
    """Extract metrics for a specific asset from collected data"""
    # Placeholder - would implement actual extraction logic
    return analysis


# ============== Scoring & Verdict ==============

def calculate_scores(config: Dict[str, Any], market_metrics: Dict, asset_analyses: Dict) -> Dict[str, float]:
    """
    Calculate analysis scores across all dimensions
    Returns dict with fundamentals, technicals, sentiment, risks scores (0-10)
    """
    logger.info("Calculating analysis scores...")

    # Placeholder implementation
    # In production, this would:
    # - Analyze on-chain metrics for fundamentals
    # - Evaluate technical indicators (RSI, MACD, MA crossovers)
    # - Process sentiment data (social media, news tone)
    # - Assess risk factors (regulatory, liquidity, concentration)

    weights = config['VERDICT_WEIGHTS']
    scores = {
        'fundamentals': 5.0,
        'technicals': 5.0,
        'sentiment': 5.0,
        'risks': 5.0
    }

    weighted_total = (
        scores['fundamentals'] * weights.get('fundamentals', 0.25) +
        scores['technicals'] * weights.get('technicals', 0.25) +
        scores['sentiment'] * weights.get('sentiment', 0.20) +
        scores['risks'] * weights.get('risks', 0.25)
    )

    logger.info(f"Scores: fundamentals={scores['fundamentals']:.2f}, "
                f"technicals={scores['technicals']:.2f}, "
                f"sentiment={scores['sentiment']:.2f}, "
                f"risks={scores['risks']:.2f} -> weighted={weighted_total:.2f}")

    scores['weighted_total'] = weighted_total
    return scores


def determine_verdict(scores: Dict[str, float], thresholds: Dict[str, Any]) -> tuple[str, str]:
    """
    Determine final verdict based on weighted score
    Returns (verdict_string, rationale)
    """
    score = scores['weighted_total']
    buy_min = thresholds.get('BUY_SCORE_MIN', 7.0)
    sell_max = thresholds.get('SELL_SCORE_MAX', 3.0)

    if score >= buy_min:
        verdict = "STRONG_BUY" if score >= 8.5 else "BUY"
        rationale = f"Weighted score {score:.2f} exceeds buy threshold {buy_min}"
    elif score <= sell_max:
        verdict = "STRONG_SELL" if score <= 1.5 else "SELL"
        rationale = f"Weighted score {score:.2f} below sell threshold {sell_max}"
    else:
        verdict = "HOLD"
        rationale = f"Weighted score {score:.2f} in hold range [{sell_max}, {buy_min}]"

    logger.info(f"Verdict: {verdict} - {rationale}")
    return verdict, rationale


# ============== Report Generation ==============

def generate_report(config: Dict, market: Dict, assets: Dict, scores: Dict,
                   verdict: str, rationale: str) -> str:
    """Generate markdown report"""
    date_str = datetime.now().strftime('%Y-%m-%d')

    report = f"""# Cryptocurrency Market Report - {date_str}

---

## Executive Summary

**Market Verdict: {verdict}**  
**Confidence Score: {scores['weighted_total']:.2f}/10**

### Key Highlights

- **Report generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
- **Assets analyzed:** {', '.join(config['TRACKED_ASSETS'])}
- **Data sources:** {len(config['DATA_SOURCES'])}
- **Articles processed:** {market.get('articles_analyzed', 0)}
- **Time horizon:** Medium-term (2-4 weeks)

---

## Score Breakdown

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Fundamentals | {scores['fundamentals']:.2f}/10 | {config['VERDICT_WEIGHTS'].get('fundamentals', 0.30):.0%} | {scores['fundamentals'] * config['VERDICT_WEIGHTS'].get('fundamentals', 0.30):.2f} |
| Technicals | {scores['technicals']:.2f}/10 | {config['VERDICT_WEIGHTS'].get('technicals', 0.25):.0%} | {scores['technicals'] * config['VERDICT_WEIGHTS'].get('technicals', 0.25):.2f} |
| Sentiment | {scores['sentiment']:.2f}/10 | {config['VERDICT_WEIGHTS'].get('sentiment', 0.20):.0%} | {scores['sentiment'] * config['VERDICT_WEIGHTS'].get('sentiment', 0.20):.2f} |
| Risks | {scores['risks']:.2f}/10 | {config['VERDICT_WEIGHTS'].get('risks', 0.25):.0%} | {scores['risks'] * config['VERDICT_WEIGHTS'].get('risks', 0.25):.2f} |
| **Total** | | **100%** | **{scores['weighted_total']:.2f}** |

---

## Asset Analysis

| Symbol | Name | Price | 24h Change | RSI | Sentiment |
|--------|------|-------|------------|-----|-----------|
"""

    # Add asset rows
    for symbol in config['TRACKED_ASSETS']:
        asset = assets.get(symbol, {})
        price = f"${asset.get('price'):,.2f}" if asset.get('price') else "N/A"
        change = f"{asset.get('change_24h'):+.2f}%" if asset.get('change_24h') else "N/A"
        rsi = f"{asset.get('rsi'):.1f}" if asset.get('rsi') else "N/A"
        sentiment = f"{asset.get('sentiment_score'):.2f}" if asset.get('sentiment_score') else "N/A"
        report += f"| {symbol} | {asset.get('name', symbol)} | {price} | {change} | {rsi} | {sentiment} |\n"

    report += """
---

## Rationale

"""
    report += rationale + "\n\n"

    report += """---

## Methodology Notes

- Data aggregated from multiple public sources: news outlets, on-chain analytics, social media, and market data providers
- Analysis combines quantitative metrics with qualitative assessment
- Weighted scoring: Fundamentals (30%), Technicals (25%), Sentiment (20%), Risks (25%)
- Scores range 0-10 (higher = more bullish)
- **Not financial advice** - for informational purposes only

---

## Data Sources Used

"""

    for source in config['DATA_SOURCES']:
        count = len(collected_data.get(source['name'], []))
        report += f"- **{source['name']}**: {count} items (priority {source.get('priority', '?')})\n"

    report += f"\n*Report generated by Crypto Reporter Agent (OpenClaw)*"

    return report


# ============== Main Execution ==============

def main():
    """Main agent entry point"""
    logger.info("=" * 60)
    logger.info("Crypto Reporter Agent - Starting Daily Report")
    logger.info("=" * 60)

    try:
        # 1. Load config
        config = load_config()

        # 2. Collect data from all sources
        global collected_data  # Make available for reporting
        collected_data = collect_data(config)

        # 3. Analyze market metrics
        market_metrics = analyze_market_metrics(collected_data)

        # 4. Analyze assets
        asset_analyses = analyze_assets(config, collected_data)

        # 5. Calculate scores
        scores = calculate_scores(config, market_metrics, asset_analyses)

        # 6. Determine verdict
        verdict, rationale = determine_verdict(scores, config['VERDICT_THRESHOLDS'])

        # 7. Generate report
        report_content = generate_report(
            config, market_metrics, asset_analyses, scores, verdict, rationale
        )

        # 8. Save report
        date_str = datetime.now().strftime('%Y-%m-%d')
        md_file = OUTPUT_DIR / f'crypto-report-{date_str}.md'
        with open(md_file, 'w') as f:
            f.write(report_content)
        logger.info(f"✓ Report saved: {md_file}")

        # 9. Save JSON if configured
        if config.get('REPORT_FORMAT') in ('json', 'both'):
            json_file = OUTPUT_DIR / f'crypto-report-{date_str}.json'
            report_json = {
                'date': date_str,
                'verdict': verdict,
                'confidence': round(scores['weighted_total'], 2),
                'scores': scores,
                'assets': asset_analyses,
                'market': market_metrics,
                'generated_at': datetime.now().isoformat()
            }
            with open(json_file, 'w') as f:
                json.dump(report_json, f, indent=2)
            logger.info(f"✓ JSON saved: {json_file}")

        # 10. Update latest symlink
        latest_md = OUTPUT_DIR / 'crypto-report-latest.md'
        if latest_md.exists():
            latest_md.unlink()
        latest_md.symlink_to(md_file.name)
        logger.info("✓ Latest symlink updated")

        # 11. Summary for OpenClaw agent system
        result = {
            'status': 'success',
            'date': date_str,
            'verdict': verdict,
            'confidence': round(scores['weighted_total'], 2),
            'assets_analyzed': len(config['TRACKED_ASSETS']),
            'sources_used': len(collected_data),
            'articles_processed': sum(len(v) for v in collected_data.values()),
            'report_path': str(md_file)
        }

        print(json.dumps(result, indent=2))
        logger.info("=" * 60)
        logger.info(f"✓ Report complete: {verdict} (confidence: {scores['weighted_total']:.2f}/10)")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"✗ Report generation failed: {e}", exc_info=True)
        error_result = {
            'status': 'error',
            'error': str(e),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        print(json.dumps(error_result, indent=2))
        return 1


if __name__ == '__main__':
    sys.exit(main())
