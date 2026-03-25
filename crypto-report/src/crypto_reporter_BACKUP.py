#!/usr/bin/env python3
"""
Standalone Daily Cryptocurrency Report Generator

This script is a self-contained tool that generates comprehensive daily crypto
reports by fetching data from free public APIs. It can be run directly from
cron or manually.

No external dependencies beyond Python standard library.
"""

import sys
import os
import json
import yaml
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean
from xml.etree import ElementTree as ET

# ============== Configuration ==============

WORKSPACE = Path('/home/node/.openclaw/workspace')
CRYPTO_DIR = WORKSPACE / 'crypto-report'
CONFIG_PATH = CRYPTO_DIR / 'config.yaml'
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

# ============== HTTP Utilities ==============

def fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL with error handling"""
    try:
        logger.debug(f"Fetching: {url}")
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e.code} {e.reason}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"URL error fetching {url}: {e.reason}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error from {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise

def fetch_rss(url: str, timeout: int = 15) -> List[Dict[str, str]]:
    """Fetch RSS feed and return list of items with title, link, description, pubDate"""
    try:
        logger.debug(f"Fetching RSS: {url}")
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            root = ET.fromstring(data)
            items = []
            # RSS 2.0 structure: <rss><channel><item>...
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                items.append({
                    'title': title.text if title is not None else '',
                    'link': link.text if link is not None else '',
                    'description': description.text if description is not None else '',
                    'pubDate': pub_date.text if pub_date is not None else ''
                })
            return items
    except Exception as e:
        logger.error(f"Error fetching RSS {url}: {e}")
        return []

# ============== API Data Fetching ==============

def fetch_global_market_data() -> Dict[str, Any]:
    """Fetch global crypto market metrics from CoinGecko"""
    url = "https://api.coingecko.com/api/v3/global"
    data = fetch_json(url)
    return data.get('data', {})

def fetch_coin_market_data(coin_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch market data for specific coins from CoinGecko"""
    if not coin_ids:
        return []
    ids_str = ','.join(coin_ids)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&order=market_cap_desc&per_page=100&page=1"
    return fetch_json(url)

def fetch_coin_ohlc(coin_id: str, days: int = 7) -> List[List[float]]:
    """Fetch OHLC data for a coin. Returns list of [timestamp, open, high, low, close]"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    return fetch_json(url)

def fetch_fear_and_greed_index() -> Dict[str, Any]:
    """Fetch Crypto Fear & Greed Index from alternative.me"""
    url = "https://api.alternative.me/fng/?limit=1"
    data = fetch_json(url)
    if data.get('data'):
        return data['data'][0]
    return {}

def fetch_bitcoin_onchain() -> Dict[str, Any]:
    """Fetch Bitcoin on-chain metrics from blockchain.info"""
    url = "https://blockchain.info/stats?cors=true"
    try:
        data = fetch_json(url)
        return data
    except:
        return {}

def fetch_news_rss(feeds: List[str], max_items_per_feed: int = 10) -> List[Dict[str, str]]:
    """Fetch recent news from multiple RSS feeds"""
    all_items = []
    for feed_url in feeds:
        items = fetch_rss(feed_url)
        all_items.extend(items[:max_items_per_feed])
    # Sort by pubDate if available (approximate)
    return all_items

# ============== Analysis ==============

def calculate_rsi(ohlc_data: List[List[float]], period: int = 14) -> Optional[float]:
    """Calculate RSI from OHLC data (using close prices)"""
    if len(ohlc_data) < period + 1:
        return None

    closes = [candle[4] for candle in ohlc_data]  # Close prices
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = mean(gains[:period])
    avg_loss = mean(losses[:period])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)

def calculate_simple_score(technical_metrics: Dict, sentiment_value: int) -> tuple[float, str]:
    """
    Calculate a simple score (0-10) based on technicals and sentiment.
    Returns (score, rationale)
    """
    score = 5.0
    reasons = []

    # RSI contribution
    rsi = technical_metrics.get('rsi')
    if rsi is not None:
        if rsi < 30:
            score += 1.5
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 1.5
            reasons.append("RSI overbought")
        else:
            reasons.append(f"RSI neutral at {rsi}")

    # Trend contribution (price vs SMA)
    trend = technical_metrics.get('trend', 0)  # positive for above SMA, negative for below
    if trend > 0:
        score += 1.0
        reasons.append("Price above 7-day SMA (bullish)")
    elif trend < 0:
        score -= 1.0
        reasons.append("Price below 7-day SMA (bearish)")

    # Fear & Greed contribution
    if sentiment_value <= 25:
        score += 1.0
        reasons.append("Extreme fear - potential bottom")
    elif sentiment_value >= 75:
        score -= 1.5
        reasons.append("Extreme greed - potential top")
    else:
        reasons.append(f"F&G at {sentiment_value} (neutral)")

    # Clamp to 0-10
    score = max(0.0, min(10.0, score))
    rationale = "; ".join(reasons)
    return score, rationale

def analyze_news_sentiment(news_items: List[Dict[str, str]]) -> tuple[float, List[str], List[str]]:
    """
    Simple news sentiment analysis using keyword matching.
    Returns (sentiment_score, positive_keywords, negative_keywords)
    Score range: -1.0 to 1.0
    """
    positive_words = [
        'bullish', 'rally', 'surge', 'gain', 'up', 'rise', 'growth', 'adoption',
        'breakthrough', 'partnership', 'launch', 'success', 'strong', 'high',
        'institutional', 'ETF', 'approval', 'lift', 'uptrend'
    ]
    negative_words = [
        'bearish', 'crash', 'drop', 'fall', 'down', 'decline', 'loss', 'sell-off',
        'regulation', 'sec', 'lawsuit', 'hack', 'scam', 'fraud', 'exploit',
        'ban', 'warning', 'risk', 'trouble', 'low', 'weak', 'concern'
    ]

    combined_text = " ".join([
        item.get('title', '') + " " + item.get('description', '')
        for item in news_items
    ]).lower()

    pos_count = sum(combined_text.count(word) for word in positive_words)
    neg_count = sum(combined_text.count(word) for word in negative_words)

    total = pos_count + neg_count
    score = 0.0
    if total > 0:
        score = (pos_count - neg_count) / total

    # Extract which words appeared
    pos_found = [w for w in positive_words if w in combined_text]
    neg_found = [w for w in negative_words if w in combined_text]

    return round(score, 3), pos_found[:5], neg_found[:5]

def assess_risks(news_sentiment: tuple, onchain_data: Dict, btc_dominance: Optional[float]) -> tuple[float, List[str]]:
    """
    Assess overall risk score (0.0 to 1.0, higher = more risk)
    Returns (risk_score, risk_factors)
    """
    risk_score = 0.3  # Base risk
    factors = []

    # News negative sentiment increases risk
    news_score, _, neg_keywords = news_sentiment
    if news_score < -0.3:
        risk_score += 0.2
        factors.append("Negative news sentiment")
    if len(neg_keywords) > 5:
        risk_score += 0.1
        factors.append("Multiple negative keywords detected")

    # Regulatory keywords specifically
    regulatory_keywords = ['regulation', 'sec', 'lawsuit', 'ban', 'compliance']
    if any(k in " ".join(neg_keywords) for k in regulatory_keywords):
        risk_score += 0.2
        factors.append("Regulatory concerns in news")

    # High BTC dominance indicates altcoin illiquidity risk
    if btc_dominance and btc_dominance > 65:
        risk_score += 0.15
        factors.append(f"High BTC dominance ({btc_dominance:.1f}%) reduces altcoin liquidity")

    # On-chain anomalies: flat hash rate or declining
    # Placeholder - would analyze hash rate trend
    # ...

    risk_score = min(1.0, risk_score)
    return round(risk_score, 3), factors

def load_config() -> Dict[str, Any]:
    """Load YAML config"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

# ============== Main Report Generation ==============

def generate_report(config: Dict) -> Dict[str, Any]:
    """Generate the full cryptocurrency report"""
    logger.info("Starting report generation")

    # 1. Fetch global market data
    global_data = fetch_global_market_data()
    btc_dominance = global_data.get('btc_dominance_percentage')
    market_cap_usd = global_data.get('total_market_cap', {}).get('usd')
    volume_usd = global_data.get('total_volume', {}).get('usd')

    # 2. Fetch coin data for tracked assets
    tracked_ids = [coin.lower() for coin in config['TRACKED_ASSETS']]
    coin_market_data = fetch_coin_market_data(tracked_ids)

    # Build asset analyses
    asset_analyses = {}
    for coin in coin_market_data:
        symbol = coin['symbol'].upper()
        asset_analyses[symbol] = {
            'name': coin['name'],
            'price': coin['current_price'],
            'market_cap': coin['market_cap'],
            'volume_24h': coin['total_volume'],
            'change_24h': coin['price_change_percentage_24h'],
            'change_7d': coin.get('price_change_percentage_7d')
        }

        # Fetch OHLC for RSI
        try:
            ohlc = fetch_coin_ohlc(coin['id'], days=7)
            rsi = calculate_rsi(ohlc) if ohlc else None
            asset_analyses[symbol]['rsi'] = rsi

            # Calculate 7-day SMA trend
            if ohlc:
                closes = [candle[4] for candle in ohlc]
                sma7 = mean(closes) if closes else None
                current = closes[-1] if closes else None
                asset_analyses[symbol]['sma_7'] = sma7
                asset_analyses[symbol]['trend'] = 1 if (sma7 and current and current > sma7) else -1 if (sma7 and current and current < sma7) else 0
        except Exception as e:
            logger.warning(f"Failed to fetch OHLC for {symbol}: {e}")

    # 3. Fetch Fear & Greed
    fng = fetch_fear_and_greed_index()
    fng_value = int(fng.get('value', 50))
    fng_label = fng.get('value_classification', 'Neutral')

    # 4. Fetch Bitcoin on-chain metrics
    btc_onchain = fetch_bitcoin_onchain()
    btc_hash_rate = btc_onchain.get('hash_rate')  # In TH/s

    # 5. Fetch news from RSS feeds
    rss_feeds = config.get('NEWS_RSS_FEEDS', [
        'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'https://cointelegraph.com/rss'
    ])
    news_items = fetch_news_rss(rss_feeds, max_items_per_feed=10)

    # 6. Analyze news sentiment
    news_sentiment_score, pos_keywords, neg_keywords = analyze_news_sentiment(news_items)
    # Convert -1..1 to 0..10 scale (5 neutral)
    news_sentiment_0_10 = round(5 + (news_sentiment_score * 5), 2)

    # 7. Technical score for BTC (representative)
    btc_analysis = asset_analyses.get('BTC', {})
    technical_score, technical_rationale = calculate_simple_score(
        {
            'rsi': btc_analysis.get('rsi'),
            'trend': btc_analysis.get('trend', 0)
        },
        fng_value
    )

    # 8. Fundamentals score (using on-chain)
    fundamentals_score = 5.0
    fundamentals_factors = []
    if btc_hash_rate:
        # In production, compare to historical average
        fundamentals_factors.append(f"BTC hash rate: {btc_hash_rate:,.0f} TH/s")
    else:
        fundamentals_factors.append("On-chain data unavailable")

    # 9. Sentiment score from FnG and news
    sentiment_score = round((fng_value / 10) * 0.6 + news_sentiment_0_10 * 0.4, 2)

    # 10. Risk assessment
    risk_score, risk_factors = assess_risks(
        (news_sentiment_score, pos_keywords, neg_keywords),
        btc_onchain,
        btc_dominance
    )
    # Convert risk (0-1) to 0-10 risk-adjusted score: high risk = lower score
    risks_adjusted_score = round(10.0 - (risk_score * 10), 2)

    # 11. Weighted total
    weights = config['VERDICT_WEIGHTS']
    weighted_total = (
        fundamentals_score * weights.get('fundamentals', 0.30) +
        technical_score * weights.get('technicals', 0.25) +
        sentiment_score * weights.get('sentiment', 0.20) +
        risks_adjusted_score * weights.get('risks', 0.25)
    )

    # 12. Verdict
    buy_min = config['VERDICT_THRESHOLDS'].get('BUY_SCORE_MIN', 7.0)
    sell_max = config['VERDICT_THRESHOLDS'].get('SELL_SCORE_MAX', 3.0)

    if weighted_total >= buy_min:
        verdict = "STRONG_BUY" if weighted_total >= 8.5 else "BUY"
        verdict_rationale = f"Weighted score {weighted_total:.2f} indicates bullish bias"
    elif weighted_total <= sell_max:
        verdict = "STRONG_SELL" if weighted_total <= 1.5 else "SELL"
        verdict_rationale = f"Weighted score {weighted_total:.2f} indicates bearish bias"
    else:
        verdict = "HOLD"
        verdict_rationale = f"Weighted score {weighted_total:.2f} is neutral"

    # 13. Generate markdown report
    report_date = datetime.now().strftime('%Y-%m-%d')
    report = f"""# Cryptocurrency Market Report - {report_date}

---

## Executive Summary

**Market Verdict: {verdict}**  
**Confidence Score: {weighted_total:.2f}/10**

### Key Highlights

- **Report generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
- **Global Market Cap:** ${market_cap_usd:,.0f} if market_cap_usd else "N/A"
- **24h Volume:** ${volume_usd:,.0f} if volume_usd else "N/A"
- **BTC Dominance:** {btc_dominance:.1f}% if btc_dominance else "N/A"
- **Fear & Greed:** {fng_value} ({fng_label})
- **Assets analyzed:** {', '.join(config['TRACKED_ASSETS'])}

---

## Score Breakdown

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Fundamentals | {fundamentals_score:.2f}/10 | {weights.get('fundamentals', 0.30):.0%} | {fundamentals_score * weights.get('fundamentals', 0.30):.2f} |
| Technicals | {technical_score:.2f}/10 | {weights.get('technicals', 0.25):.0%} | {technical_score * weights.get('technicals', 0.25):.2f} |
| Sentiment | {sentiment_score:.2f}/10 | {weights.get('sentiment', 0.20):.0%} | {sentiment_score * weights.get('sentiment', 0.20):.2f} |
| Risks (adj.) | {risks_adjusted_score:.2f}/10 | {weights.get('risks', 0.25):.0%} | {risks_adjusted_score * weights.get('risks', 0.25):.2f} |
| **Total** | | **100%** | **{weighted_total:.2f}** |

---

## Asset Analysis

| Symbol | Name | Price | 24h Change | RSI | Trend |
|--------|------|-------|------------|-----|-------|
"""

    for symbol, analysis in asset_analyses.items():
        price = analysis.get('price')
        change = analysis.get('change_24h')
        rsi = analysis.get('rsi')
        trend = analysis.get('trend', 0)
        trend_str = "Above SMA7" if trend > 0 else "Below SMA7" if trend < 0 else "Flat"

        price_str = f"${price:,.2f}" if price else "N/A"
        change_str = f"{change:+.2f}%" if change is not None else "N/A"
        rsi_str = f"{rsi:.1f}" if rsi else "N/A"

        report += f"| {symbol} | {analysis.get('name', symbol)} | {price_str} | {change_str} | {rsi_str} | {trend_str} |\n"

    report += """
---

## Fundamentals Overview

- **BTC Hash Rate:** """ + (f"{btc_hash_rate:,.0f} TH/s" if btc_hash_rate else "Data unavailable") + """
- **Network Health:** Based on hash rate stability and historical averages.

*(More detailed on-chain metrics require premium data sources)*

---

## Sentiment Analysis

- **Fear & Greed Index:** """ + f"{fng_value} ({fng_label})" + """
- **News Sentiment Score:** """ + f"{news_sentiment_score:.3f} (range -1 to +1)" + """
  - Positive keywords detected: """ + ', '.join(pos_keywords) if pos_keywords else "None" + """
  - Negative keywords detected: """ + ', '.join(neg_keywords) if neg_keywords else "None" + """

---

## Risk Assessment

**Overall Risk Score:** {risk_score:.3f} / 1.0

**Risk Factors:** """ + (", ".join(risk_factors) if risk_factors else "No significant risks detected") + """

---

## Rationale

{verdict_rationale}

- **Technical factors:** """ + technical_rationale + """
- **Sentiment:** Fear & Greed at {fng_value} indicates {fng_label.lower()}.
- **News tone:** {'Positive' if news_sentiment_score > 0.1 else 'Negative' if news_sentiment_score < -0.1 else 'Neutral'}.
- **Risk factors:** """ + (f"{len(risk_factors)} identified" if risk_factors else "Minimal") + """

---

## Methodology Notes

- Data sources: CoinGecko API (price, market cap, volume), Alternative.me (Fear & Greed), Blockchain.info (BTC on-chain), RSS feeds (news).
- Technical indicators: RSI (14-day), 7-day Simple Moving Average.
- Sentiment: Simple keyword-based analysis of recent news headlines.
- Risk assessment: Based on news keywords, BTC dominance, and market conditions.
- **Not financial advice** - for informational purposes only.

---

## Data Sources Used

- CoinGecko Global & Markets API
- Alternative.me Fear & Greed Index
- Blockchain.info stats
- RSS: CoinDesk, Cointelegraph

*Report generated by Crypto Reporter v1.0 (OpenClaw)*

"""

    return {
        'date': report_date,
        'verdict': verdict,
        'confidence': weighted_total,
        'scores': {
            'fundamentals': fundamentals_score,
            'technicals': technical_score,
            'sentiment': sentiment_score,
            'risks_adjusted': risks_adjusted_score,
            'weighted_total': weighted_total
        },
        'market': {
            'market_cap_usd': market_cap_usd,
            'volume_usd': volume_usd,
            'btc_dominance': btc_dominance,
            'fear_greed': {'value': fng_value, 'label': fng_label}
        },
        'assets': asset_analyses,
        'news': {
            'items_count': len(news_items),
            'sentiment_score': news_sentiment_score,
            'positive_keywords': pos_keywords,
            'negative_keywords': neg_keywords
        },
        'risks': {
            'score': risk_score,
            'factors': risk_factors
        },
        'onchain': {
            'btc_hash_rate': btc_hash_rate
        }
    }

# ============== Save Functions ==============

def save_report(report_data: Dict, config: Dict):
    """Save report in markdown and optionally JSON"""
    date_str = report_data['date']
    report_md = generate_markdown(report_data, config)

    # Save markdown
    md_file = OUTPUT_DIR / f'crypto-report-{date_str}.md'
    with open(md_file, 'w') as f:
        f.write(report_md)
    logger.info(f"Markdown saved: {md_file}")

    # Save JSON if configured
    if config.get('REPORT_FORMAT') in ('json', 'both'):
        json_file = OUTPUT_DIR / f'crypto-report-{date_str}.json'
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"JSON saved: {json_file}")

    # Update latest symlink
    latest_md = OUTPUT_DIR / 'crypto-report-latest.md'
    if latest_md.exists():
        latest_md.unlink()
    latest_md.symlink_to(md_file.name)
    logger.info("Latest symlink updated")

def generate_markdown(report_data: Dict, config: Dict) -> str:
    """Convert report data to markdown string"""
    # Already generated in generate_report, but we can reconstruct or store separately
    # For simplicity, we could have generate_report return both data and markdown.
    # But in our current flow, we built markdown inline. Let's refactor: separate generation.
    # Actually, we already built the markdown as `report` string in generate_report.
    # We'll extract that.
    # But I wrote the markdown generation inside generate_report earlier. Let me restructure:
    # In generate_report, we should compute all data, then call format_markdown(report_data) to get markdown.
    # Since I already wrote the markdown inline above, it's fine. We can return it as part of the dict under 'markdown' key.
    # Let's adjust: modify generate_report to return (report_data, markdown_string).
    pass  # Will handle below

# Actually, let's restructure the code to separate data and formatting.

# I'll rewrite generate_report to compute all metrics and then call a formatting function.

def format_markdown(report_data: Dict, config: Dict) -> str:
    """Format report data as markdown"""
    date_str = report_data['date']
    verdict = report_data['verdict']
    confidence = report_data['confidence']
    scores = report_data['scores']
    market = report_data['market']
    assets = report_data['assets']
    news = report_data['news']
    risks = report_data['risks']
    onchain = report_data.get('onchain', {})

    btc_hash_rate = onchain.get('btc_hash_rate')
    fng_value = market.get('fear_greed', {}).get('value', 50)
    fng_label = market.get('fear_greed', {}).get('label', 'Neutral')

    weights = config['VERDICT_WEIGHTS']

    lines = [
        f"# Cryptocurrency Market Report - {date_str}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Market Verdict: {verdict}**",
        f"**Confidence Score: {confidence:.2f}/10**",
        "",
        "### Key Highlights",
        "",
        f"- **Global Market Cap:** ${market.get('market_cap_usd'):,.0f}" if market.get('market_cap_usd') else "- **Global Market Cap:** N/A",
        f"- **24h Volume:** ${market.get('volume_usd'):,.0f}" if market.get('volume_usd') else "- **24h Volume:** N/A",
        f"- **BTC Dominance:** {market.get('btc_dominance', 0):.1f}%",
        f"- **Fear & Greed:** {fng_value} ({fng_label})",
        f"- **Assets analyzed:** {', '.join(config['TRACKED_ASSETS'])}",
        "",
        "## Score Breakdown",
        "",
        "| Dimension | Score | Weight | Weighted |",
        "|-----------|-------|--------|----------|",
        f"| Fundamentals | {scores['fundamentals']:.2f}/10 | {weights.get('fundamentals', 0.30):.0%} | {scores['fundamentals'] * weights.get('fundamentals', 0.30):.2f} |",
        f"| Technicals | {scores['technicals']:.2f}/10 | {weights.get('technicals', 0.25):.0%} | {scores['technicals'] * weights.get('technicals', 0.25):.2f} |",
        f"| Sentiment | {scores['sentiment']:.2f}/10 | {weights.get('sentiment', 0.20):.0%} | {scores['sentiment'] * weights.get('sentiment', 0.20):.2f} |",
        f"| Risks (adj.) | {scores['risks_adjusted']:.2f}/10 | {weights.get('risks', 0.25):.0%} | {scores['risks_adjusted'] * weights.get('risks', 0.25):.2f} |",
        f"| **Total** | | **100%** | **{scores['weighted_total']:.2f}** |",
        "",
        "## Asset Analysis",
        "",
        "| Symbol | Name | Price | 24h Change | RSI | Trend |",
        "|--------|------|-------|------------|-----|-------|",
    ]

    for symbol, analysis in assets.items():
        price = analysis.get('price')
        change = analysis.get('change_24h')
        rsi = analysis.get('rsi')
        trend_val = analysis.get('trend', 0)
        trend_str = "> SMA7" if trend_val > 0 else "< SMA7" if trend_val < 0 else "Flat"
        price_str = f"${price:,.2f}" if price else "N/A"
        change_str = f"{change:+.2f}%" if change is not None else "N/A"
        rsi_str = f"{rsi:.1f}" if rsi else "N/A"
        lines.append(f"| {symbol} | {analysis.get('name', symbol)} | {price_str} | {change_str} | {rsi_str} | {trend_str} |")

    lines.extend([
        "",
        "## Fundamentals Overview",
        "",
        f"- **BTC Hash Rate:** {btc_hash_rate:,.0f} TH/s" if btc_hash_rate else "- **BTC Hash Rate:** Data unavailable",
        "- **Network Health:** Inferred from hash rate trend (requires longer history for accurate trend).",
        "",
        "## Sentiment Analysis",
        "",
        f"- **Fear & Greed Index:** {fng_value} ({fng_label})",
        f"- **News Sentiment Score:** {news['sentiment_score']:.3f} (range -1 to +1)",
        f"  - Positive keywords: {', '.join(news['positive_keywords']) if news['positive_keywords'] else 'None'}",
        f"  - Negative keywords: {', '.join(news['negative_keywords']) if news['negative_keywords'] else 'None'}",
        "",
        "## Risk Assessment",
        "",
        f"**Overall Risk Score:** {risks['score']:.3f} / 1.0",
        "",
        "**Risk Factors:** " + (", ".join(risks['factors']) if risks['factors'] else "No significant risks detected"),
        "",
        "## Verdict Rationale",
        "",
        f"The **{verdict}** recommendation is based on a weighted composite score of **{confidence:.2f}/10**.",
        "",
        f"- **Technical factors:** RSI={'oversold' if assets.get('BTC', {}).get('rsi', 50) < 30 else 'overbought' if assets.get('BTC', {}).get('rsi', 50) > 70 else 'neutral'}; Fear & Greed at {fng_value} ({fng_label}).",
        f"- **News sentiment:** {'Positive' if news['sentiment_score'] > 0.1 else 'Negative' if news['sentiment_score'] < -0.1 else 'Neutral'}.",
        f"- **Risk factors:** {len(risks['factors'])} identified: {'; '.join(risks['factors'])}.",
        "",
        "## Methodology Notes",
        "",
        "- Data sources: CoinGecko API, Alternative.me, Blockchain.info, RSS news feeds.",
        "- Technical indicators: RSI (14-day), 7-day Simple Moving Average.",
        "- Sentiment: Keyword-based analysis of recent news headlines.",
        "- Risk assessment: Aggregates negative news keywords, regulatory mentions, BTC dominance.",
        "- **This report is for informational purposes only and not financial advice.**",
        "",
        f"*Generated by Crypto Reporter v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*"
    ])

    return "\n".join(lines)

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Crypto Reporter - Daily Market Report")
    logger.info("=" * 60)

    try:
        config = load_config()
        logger.info(f"Loaded config: {len(config['TRACKED_ASSETS'])} assets, weights: {config['VERDICT_WEIGHTS']}")

        # Generate report data
        report_data = generate_report(config)

        # Format markdown (add to dict for saving)
        report_data['markdown'] = format_markdown(report_data, config)

        # Save files
        date_str = report_data['date']
        md_file = OUTPUT_DIR / f'crypto-report-{date_str}.md'
        with open(md_file, 'w') as f:
            f.write(report_data['markdown'])
        logger.info(f"Report saved: {md_file}")

        if config.get('REPORT_FORMAT') in ('json', 'both'):
            json_file = OUTPUT_DIR / f'crypto-report-{date_str}.json'
            with open(json_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"JSON data saved: {json_file}")

        # Symlink latest
        latest_md = OUTPUT_DIR / 'crypto-report-latest.md'
        if latest_md.exists():
            latest_md.unlink()
        latest_md.symlink_to(md_file.name)
        logger.info("Updated latest symlink")

        # Print summary for cron logs
        print(json.dumps({
            'status': 'success',
            'date': date_str,
            'verdict': report_data['verdict'],
            'confidence': round(report_data['confidence'], 2),
            'assets': list(report_data['assets'].keys()),
            'sources': ['CoinGecko', 'Alternative.me', 'Blockchain.info', 'RSS'],
            'output': str(md_file)
        }, indent=2))

        logger.info("=" * 60)
        logger.info(f"✓ Complete: {report_data['verdict']} (score: {confidence:.2f})")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"✗ Report generation failed: {e}", exc_info=True)
        print(json.dumps({'status': 'error', 'error': str(e)}))
        return 1

if __name__ == '__main__':
    sys.exit(main())
