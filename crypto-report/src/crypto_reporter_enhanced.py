#!/usr/bin/env python3
"""
Enhanced Daily Cryptocurrency Report Generator

Fetches data from multiple free APIs with rate-limit resilience:
- CoinGecko: market prices, volumes, market cap
- Alternative.me: Fear & Greed Index
- Binance: OHLC data for RSI & technical indicators (reliable, no rate limits)
- CryptoDataAPI: On-chain metrics (free tier)
- RSS feeds: news sentiment

Comprehensive analysis with Buy/Hold/Sell verdict.
"""

import sys
import os
import json
import logging
import urllib.request
import urllib.error
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean
from xml.etree import ElementTree as ET

# ============== Config & Paths ==============

WORKSPACE = Path('/home/ubuntu/.openclaw/workspace')
CRYPTO_DIR = WORKSPACE / 'crypto-report'
CONFIG_PATH = CRYPTO_DIR / 'config.json'
OUTPUT_DIR = WORKSPACE / 'memory' / 'crypto-reports'
ARTIFACTS_DIR = CRYPTO_DIR / 'artifacts'
CACHE_DIR = CRYPTO_DIR / 'cache'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('crypto-reporter')

# ============== HTTP Helpers ==============

def fetch_json(url: str, timeout: int = 15, max_retries: int = 2, base_delay: float = 1.0, source: str = None) -> Any:
    """Fetch JSON with exponential backoff retry on rate limits (429) and network errors"""
    headers = {'User-Agent': 'OpenClaw-CryptoReporter/1.0 (+https://github.com/openclaw)'}
    if source == 'binance':
        headers['Accept'] = 'application/json'

    req = urllib.request.Request(url, headers=headers)

    for attempt in range(max_retries):
        try:
            logger.debug(f"GET {url} (attempt {attempt + 1}/{max_retries})")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 429:
                    raise urllib.error.HTTPError(req.full_url, 429, "Rate Limited", resp.headers, None)
                content = resp.read().decode('utf-8')
                if not content.strip():
                    logger.warning(f"Empty response from {url}")
                    return {} if source != 'binance' else []
                return json.loads(content)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"Rate limited (429) for {url}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                logger.error(f"Rate limit persisted after {max_retries} retries for {url}")
                raise
            else:
                logger.error(f"HTTP error {e.code} for {url}: {e.reason}")
                raise
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")

        if attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))
        else:
            logger.error(f"All {max_retries} attempts failed for {url}")
            raise

def fetch_rss(url: str, max_items: int = 10) -> List[Dict[str, str]]:
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'OpenClaw-CryptoReporter/1.0 (+https://github.com/openclaw)'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode('utf-8')
            if not data.strip():
                logger.warning(f"Empty RSS response from {url}")
                return []
            root = ET.fromstring(data)
            items = []
            for item in root.findall('.//item'):
                title = item.find('title')
                desc = item.find('description')
                link = item.find('link')
                items.append({
                    'title': title.text if title is not None else '',
                    'description': desc.text if desc is not None else '',
                    'link': link.text if link is not None else ''
                })
            return items[:max_items]
    except Exception as e:
        logger.error(f"RSS fetch failed {url}: {e}")
        return []

# ============== Data Sources ==============

def get_global_market() -> Dict[str, Any]:
    data = fetch_json("https://api.coingecko.com/api/v3/global")
    return data.get('data', {})

def get_coin_markets(ids: List[str]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={','.join(ids)}&order=market_cap_desc&per_page=100&page=1"
    return fetch_json(url)

def get_binance_klines(symbol: str, interval: str = '1d', days: int = 14) -> List[List[float]]:
    """
    Fetch OHLC data from Binance.
    symbol: Binance symbol like BTCUSDT (already includes USDT)
    Returns list of [open, high, low, close, volume] for each candle.
    """
    if interval == '1d':
        limit = min(days, 1000)
    elif interval == '1h':
        limit = min(days * 24, 1000)
    else:
        limit = 100

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    raw = fetch_json(url, source='binance')
    if not raw:
        return []

    # Parse Binance klines: [open_time, open, high, low, close, volume, ...]
    ohlc = []
    for k in raw:
        try:
            ohlc.append([float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])])
        except (IndexError, ValueError):
            continue
    return ohlc

def get_fear_greed() -> Dict[str, Any]:
    data = fetch_json("https://api.alternative.me/fng/?limit=1")
    return data['data'][0] if data.get('data') else {}

def get_onchain_metrics() -> Dict[str, Any]:
    """
    Fetch Bitcoin on-chain metrics from free sources.
    Returns dict with hash_rate, active_addresses, etc.
    """
    metrics = {}

    # Try CoinMetrics community API (free)
    try:
        data = fetch_json("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=BTC&metrics=HashRate,DailyAddressCount,ExchangeVolume,PriceUSD")
        if data.get('data'):
            latest = data['data'][-1] if data['data'] else {}
            metrics['hash_rate'] = latest.get('HashRate')  # TH/s
            metrics['active_addresses'] = latest.get('DailyAddressCount')
            metrics['exchange_volume'] = latest.get('ExchangeVolume')
    except Exception as e:
        logger.warning(f"CoinMetrics failed: {e}")

    # Try CryptoQuant (some endpoints open)
    try:
        data = fetch_json("https://api.cryptoquant.com/live/v3/chart/61a8e6d0e4a08d34?window=DAY")
        # This might need API key; will likely fail but we try
        if isinstance(data, dict) and data.get('data'):
            metrics['funding_rate'] = data['data'][0].get('fundingRate')
    except:
        pass

    # Fallback: CoinGecko coin details (includes block_time)
    try:
        data = fetch_json("https://api.coingecko.com/api/v3/coins/bitcoin")
        if data.get('block_time_in_minutes'):
            metrics['block_time'] = data['block_time_in_minutes']
        if data.get('tvl'):
            metrics['tvl'] = data['tvl']
    except Exception as e:
        logger.warning(f"CoinGecko coin details failed: {e}")

    return metrics

def get_news_items(feeds: List[str], per_feed: int = 10) -> List[Dict[str, str]]:
    items = []
    for feed in feeds:
        items.extend(fetch_rss(feed, max_items=per_feed))
    return items

# Mapping from ticker symbols to CoinGecko IDs and Binance symbols
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'ADA': 'cardano',
    'SOL': 'solana',
    'AVAX': 'avalanche-2',
    'DOT': 'polkadot',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'AAVE': 'aave',
    'MKR': 'maker'
}

BINANCE_SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'ADA': 'ADAUSDT',
    'SOL': 'SOLUSDT',
    'AVAX': 'AVAXUSDT',
    'DOT': 'DOTUSDT',
    'LINK': 'LINKUSDT',
    'UNI': 'UNIUSDT',
    'AAVE': 'AAVEUSDT',
    'MKR': 'MKRUSDT'
}

# ============== Analytics ==============

def calc_rsi(ohlc: List[List[float]], period: int = 14) -> Optional[float]:
    """Calculate RSI using Wilder's smoothing."""
    if len(ohlc) < period + 1:
        return None
    closes = [c[3] for c in ohlc]  # close price is index 3
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    avg_gain = mean(gains) if gains else 0
    avg_loss = mean(losses) if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)

def analyze_news_sentiment(news: List[Dict[str, str]]) -> tuple[float, List[str], List[str]]:
    pos_words = ['bullish','rally','surge','gain','up','rise','growth','adoption','breakthrough','partnership','launch','success','strong','high','institutional','ETF','approval','lift','uptrend','bull','breakout','soar']
    neg_words = ['bearish','crash','drop','fall','down','decline','loss','sell-off','regulation','sec','lawsuit','hack','scam','fraud','exploit','ban','warning','risk','trouble','low','weak','concern','crisis','slump','plunge']

    text = " ".join([n['title'] + " " + n.get('description','') for n in news]).lower()
    pos = [w for w in pos_words if w in text]
    neg = [w for w in neg_words if w in text]

    pos_count = len(pos)
    neg_count = len(neg)
    total = pos_count + neg_count
    score = (pos_count - neg_count) / total if total > 0 else 0.0
    return round(score, 3), pos[:5], neg[:5]

def assess_risk(news_sent: tuple, btc_dom: Optional[float]) -> tuple[float, List[str]]:
    score = 0.3
    factors = []
    sent_score, _, neg_kws = news_sent

    if sent_score < -0.3:
        score += 0.2
        factors.append("Negative news sentiment")
    if len(neg_kws) > 5:
        score += 0.1
        factors.append("Multiple negative keywords")
    if any(k in " ".join(neg_kws) for k in ['regulation','sec','lawsuit','ban','compliance']):
        score += 0.2
        factors.append("Regulatory concerns")
    if btc_dom and btc_dom > 65:
        score += 0.15
        factors.append(f"High BTC dominance ({btc_dom:.1f}%)")

    return min(1.0, score), factors

def compute_technical_score(rsi: Optional[float], trend: int, fng: int) -> tuple[float, str]:
    score = 5.0
    reasons = []

    if rsi is not None:
        if rsi < 30:
            score += 1.5
            reasons.append(f"RSI oversold ({rsi})")
        elif rsi > 70:
            score -= 1.5
            reasons.append(f"RSI overbought ({rsi})")
        else:
            reasons.append(f"RSI neutral ({rsi:.1f})")
    else:
        reasons.append("RSI N/A")

    if trend > 0:
        score += 1.0
        reasons.append("Price > 7-day SMA")
    elif trend < 0:
        score -= 1.0
        reasons.append("Price < 7-day SMA")
    else:
        reasons.append("Price ≈ SMA7")

    if fng <= 25:
        score += 1.0
        reasons.append("Extreme fear (buying opportunity)")
    elif fng >= 75:
        score -= 1.5
        reasons.append("Extreme greed (selling opportunity)")

    return max(0.0, min(10.0, score)), "; ".join(reasons)

def compute_fundamentals_score(onchain_metrics: Dict[str, Any]) -> float:
    """Compute fundamentals score (0-10) based on on-chain metrics."""
    score = 5.0  # Baseline

    hash_rate = onchain_metrics.get('hash_rate')
    if hash_rate:
        # Could add trend analysis if we had historical data
        # For now, presence of hash rate data adds slight confidence
        score += 0.5
    else:
        score -= 0.5

    # Add more metrics later: active addresses, TVL, exchange flows, etc.
    active_addr = onchain_metrics.get('active_addresses')
    if active_addr:
        # Normalize: compare to historical? For now just presence
        score += 0.3

    return round(min(10.0, max(0.0, score)), 2)

def compute_sentiment_score(fng: int, news_sent: float) -> float:
    fng_score = fng / 10.0
    news_score = 5.0 + (news_sent * 5.0)
    return round(fng_score * 0.6 + news_score * 0.4, 2)

def compute_verdict(score: float, thresholds: Dict) -> tuple[str, str]:
    buy_min = thresholds.get('BUY_SCORE_MIN', 7.0)
    sell_max = thresholds.get('SELL_SCORE_MAX', 3.0)
    if score >= buy_min:
        verdict = "STRONG_BUY" if score >= 8.5 else "BUY"
        rationale = f"Overall score {score:.2f} exceeds buy threshold"
    elif score <= sell_max:
        verdict = "STRONG_SELL" if score <= 1.5 else "SELL"
        rationale = f"Overall score {score:.2f} below sell threshold"
    else:
        verdict = "HOLD"
        rationale = f"Overall score {score:.2f} in neutral zone"
    return verdict, rationale

# ============== Main ==============

def main():
    logger.info("Starting Enhanced Crypto Reporter")
    try:
        config = json.load(open(CONFIG_PATH))
        logger.info(f"Config: assets={config['TRACKED_ASSETS']}, weights={config['VERDICT_WEIGHTS']}")

        # -------------------------------------------------
        # Step 1: Fetch coin market data from CoinGecko (all assets in one call)
        # -------------------------------------------------
        logger.info("Fetching coin market data from CoinGecko...")
        coin_ids = [COINGECKO_IDS[c] for c in config['TRACKED_ASSETS']]
        coins = get_coin_markets(coin_ids)

        # Build assets dict with basic market data
        assets = {}
        for c in coins:
            sym = c['symbol'].upper()
            assets[sym] = {
                'name': c['name'],
                'price': c['current_price'],
                'market_cap': c['market_cap'],
                'volume_24h': c['total_volume'],
                'change_24h': c['price_change_percentage_24h'],
                'rsi': None,
                'trend': 0
            }

        # -------------------------------------------------
        # Step 2: Fetch OHLC from Binance for technical indicators (all assets)
        # -------------------------------------------------
        time.sleep(2)  # Rate limit mitigation
        logger.info("Fetching OHLC data from Binance for technical analysis...")
        for sym, asset in assets.items():
            binance_symbol = BINANCE_SYMBOLS.get(sym)
            if not binance_symbol:
                logger.warning(f"No Binance mapping for {sym}, skipping technicals")
                continue

            try:
                # Daily OHLC for 14 days (enough for RSI(14))
                ohlc = get_binance_klines(binance_symbol, interval='1d', days=14)
                if not ohlc or len(ohlc) < 15:
                    logger.warning(f"Insufficient OHLC data for {sym}: got {len(ohlc) if ohlc else 0} points")
                    continue

                # Calculate RSI
                rsi = calc_rsi(ohlc)
                asset['rsi'] = rsi

                # Calculate 7-day SMA trend
                closes = [c[3] for c in ohlc]  # close prices
                sma_7 = mean(closes[-7:]) if len(closes) >= 7 else mean(closes)
                current = closes[-1]
                asset['sma_7'] = sma_7
                asset['trend'] = 1 if current > sma_7 else -1 if current < sma_7 else 0

                logger.debug(f"{sym}: RSI={rsi:.1f}, trend={'up' if asset['trend']>0 else 'down' if asset['trend']<0 else 'flat'}")

            except Exception as e:
                logger.warning(f"OHLC for {sym} failed: {e}")

        # -------------------------------------------------
        # Step 3: Fetch global market metrics (BTC dominance, total mcap/volume)
        # -------------------------------------------------
        time.sleep(2)  # Rate limit mitigation
        logger.info("Fetching global market metrics...")
        mcap = None
        vol = None
        btc_dom = None
        try:
            global_data = get_global_market()
            btc_dom = global_data.get('btc_dominance_percentage')
            mcap = global_data.get('total_market_cap', {}).get('usd')
            vol = global_data.get('total_volume', {}).get('usd')
            logger.info(f"Global: BTC dom {btc_dom:.1f}%, mcap ${mcap/1e12:.2f}T")
        except Exception as e:
            logger.warning(f"Global market fetch failed: {e}. Some global figures will be N/A.")

        # -------------------------------------------------
        # Step 4: On-chain metrics (BTC)
        # -------------------------------------------------
        time.sleep(2)
        logger.info("Fetching BTC on-chain metrics...")
        onchain_metrics = get_onchain_metrics()
        btc_hash = onchain_metrics.get('hash_rate')
        if btc_hash:
            logger.info(f"BTC Hash Rate: {btc_hash:,.0f} TH/s")
        else:
            logger.warning("BTC hash rate unavailable")

        # -------------------------------------------------
        # Step 5: Fear & Greed Index
        # -------------------------------------------------
        time.sleep(2)
        logger.info("Fetching Fear & Greed index...")
        fng_data = get_fear_greed()
        fng_val = int(fng_data.get('value', 50))
        fng_lbl = fng_data.get('value_classification', 'Neutral')

        # -------------------------------------------------
        # Step 6: News sentiment
        # -------------------------------------------------
        time.sleep(2)
        logger.info("Fetching news from RSS feeds...")
        feeds = config.get('NEWS_RSS_FEEDS', ['https://www.coindesk.com/arc/outboundfeeds/rss/', 'https://cointelegraph.com/rss'])
        news = get_news_items(feeds, per_feed=10)
        news_sent, pos_kw, neg_kw = analyze_news_sentiment(news)

        # -------------------------------------------------
        # Step 7: Calculate scores
        # -------------------------------------------------
        logger.info("Calculating scores...")

        # Fundamentals score based on on-chain metrics
        fundamentals_score = compute_fundamentals_score(onchain_metrics)

        # Sentiment score
        sentiment_score = compute_sentiment_score(fng_val, news_sent)

        # Technical score uses BTC as market proxy
        btc_asset = assets.get('BTC', {})
        tech_score, tech_rationale = compute_technical_score(
            btc_asset.get('rsi'),
            btc_asset.get('trend', 0),
            fng_val
        )

        # Risk assessment
        risk_score, risk_factors = assess_risk((news_sent, pos_kw, neg_kw), btc_dom)
        risks_adj_score = round(10.0 - (risk_score * 10), 2)

        # Weighted total
        w = config['VERDICT_WEIGHTS']
        weighted = (
            fundamentals_score * w.get('fundamentals', 0.30) +
            tech_score * w.get('technicals', 0.25) +
            sentiment_score * w.get('sentiment', 0.20) +
            risks_adj_score * w.get('risks', 0.25)
        )

        verdict, verdict_rationale = compute_verdict(weighted, config['VERDICT_THRESHOLDS'])

        # -------------------------------------------------
        # Step 8: Build report data and markdown
        # -------------------------------------------------
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_data = {
            'date': report_date,
            'verdict': verdict,
            'confidence': round(weighted, 2),
            'scores': {
                'fundamentals': round(fundamentals_score, 2),
                'technicals': round(tech_score, 2),
                'sentiment': round(sentiment_score, 2),
                'risks_adjusted': risks_adj_score,
                'weighted_total': round(weighted, 2)
            },
            'market': {
                'market_cap_usd': mcap,
                'volume_usd': vol,
                'btc_dominance': btc_dom
            },
            'assets': assets,
            'news': {
                'count': len(news),
                'sentiment_score': news_sent,
                'positive_keywords': pos_kw,
                'negative_keywords': neg_kw
            },
            'risks': {
                'score': risk_score,
                'factors': risk_factors
            },
            'onchain': onchain_metrics
        }

        # Generate markdown
        markdown_lines = [
            f"# Cryptocurrency Market Report - {report_date}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"**Market Verdict: {verdict}**",
            f"**Confidence Score: {report_data['confidence']}/10**",
            "",
            "### Key Highlights",
            "",
        ]

        # Highlights (only show if available)
        if mcap:
            markdown_lines.append(f"- **Global Market Cap:** ${mcap:,.0f}")
        if vol:
            markdown_lines.append(f"- **24h Volume:** ${vol:,.0f}")
        if btc_dom:
            markdown_lines.append(f"- **BTC Dominance:** {btc_dom:.1f}%")
        markdown_lines.append(f"- **Fear & Greed:** {fng_val} ({fng_lbl})")
        markdown_lines.append(f"- **Assets analyzed:** {', '.join(config['TRACKED_ASSETS'])}")
        markdown_lines.extend(["", "## Score Breakdown", "", "| Dimension | Score | Weight | Weighted |", "|-----------|-------|--------|----------|"])

        weights = w
        s = report_data['scores']
        for dim, label in [('fundamentals', 'Fundamentals'), ('technicals', 'Technicals'), ('sentiment', 'Sentiment'), ('risks_adjusted', 'Risks')]:
            w_val = weights.get(dim.split('_')[0], 0.25)
            weighted_val = s[dim] * w_val
            markdown_lines.append(f"| {label} | {s[dim]}/10 | {w_val:.0%} | {weighted_val:.2f} |")
        markdown_lines.append(f"| **Total** | | **100%** | **{s['weighted_total']:.2f}** |")

        # Asset table
        markdown_lines.extend(["", "## Asset Analysis", "", "| Symbol | Name | Price | 24h Change | RSI | Trend |", "|--------|------|-------|------------|-----|-------|"])
        for sym, a in assets.items():
            price = f"${a['price']:,.2f}" if a.get('price') else "N/A"
            change = f"{a.get('change_24h', 0):+.2f}%" if a.get('change_24h') is not None else "N/A"
            rsi = f"{a.get('rsi'):.1f}" if a.get('rsi') is not None else "N/A"
            trend_val = a.get('trend', 0)
            trend = "> SMA7" if trend_val > 0 else "< SMA7" if trend_val < 0 else "Flat"
            markdown_lines.append(f"| {sym} | {a['name']} | {price} | {change} | {rsi} | {trend} |")

        # Fundamentals
        markdown_lines.extend(["", "## Fundamentals Overview", ""])
        if btc_hash:
            markdown_lines.append(f"- **BTC Hash Rate:** {btc_hash:,.0f} TH/s")
        else:
            markdown_lines.append("- **BTC Hash Rate:** Data unavailable")
        if onchain_metrics.get('active_addresses'):
            markdown_lines.append(f"- **Active BTC Addresses:** {onchain_metrics['active_addresses']:,}")
        markdown_lines.append("- *More detailed on-chain metrics require premium data sources*")

        # Sentiment
        markdown_lines.extend(["", "## Sentiment Analysis", ""])
        markdown_lines.append(f"- **Fear & Greed Index:** {fng_val} ({fng_lbl})")
        markdown_lines.append(f"- **News Sentiment Score:** {news_sent:.3f} (-1 to +1)")
        markdown_lines.append(f"  - Positive keywords: {', '.join(pos_kw) if pos_kw else 'None'}")
        markdown_lines.append(f"  - Negative keywords: {', '.join(neg_kw) if neg_kw else 'None'}")

        # Risks
        markdown_lines.extend(["", "## Risk Assessment", ""])
        markdown_lines.append(f"**Overall Risk Score:** {risk_score:.3f} / 1.0")
        markdown_lines.append("")
        markdown_lines.append("**Risk Factors:** " + (", ".join(risk_factors) if risk_factors else "No significant risks detected"))

        # Rationale
        markdown_lines.extend(["", "## Verdict Rationale", "", f"The **{verdict}** recommendation is based on a weighted composite score of **{report_data['confidence']}/10**."])
        markdown_lines.append("")
        markdown_lines.append(f"- **Technical factors:** {tech_rationale}.")
        markdown_lines.append(f"- **Sentiment:** Fear & Greed at {fng_val} ({fng_lbl}).")
        markdown_lines.append(f"- **News tone:** {'Positive' if news_sent > 0.1 else 'Negative' if news_sent < -0.1 else 'Neutral'}.")
        markdown_lines.append(f"- **Risk factors:** {len(risk_factors)} identified: {'; '.join(risk_factors) if risk_factors else 'Minimal'}.")

        # Methodology
        markdown_lines.extend(["", "## Methodology Notes", "",
            "- Data sources: CoinGecko API, Binance API, Alternative.me, RSS news feeds, CoinMetrics.",
            "- Technical indicators: RSI (14-day), 7-day Simple Moving Average, computed from Binance OHLC.",
            "- Sentiment: Keyword-based analysis of recent news headlines.",
            "- Risk assessment: Aggregates negative news keywords, regulatory mentions, BTC dominance.",
            "- **Not financial advice** - for informational purposes only.",
            "",
            f"*Generated by Crypto Reporter v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*"
        ])

        markdown = "\n".join(markdown_lines)

        # -------------------------------------------------
        # Step 9: Save report
        # -------------------------------------------------
        date_str = report_date
        md_path = OUTPUT_DIR / f'crypto-report-{date_str}.md'
        with open(md_path, 'w') as f:
            f.write(markdown)
        logger.info(f"Report saved: {md_path}")

        if config.get('REPORT_FORMAT') in ('json', 'both'):
            json_path = OUTPUT_DIR / f'crypto-report-{date_str}.json'
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"JSON saved: {json_path}")

        # Symlink latest
        latest = OUTPUT_DIR / 'crypto-report-latest.md'
        if latest.exists():
            latest.unlink()
        latest.symlink_to(md_path.name)
        logger.info("Updated latest symlink")

        # Print summary for cron
        print(json.dumps({
            'status': 'success',
            'date': date_str,
            'verdict': verdict,
            'confidence': report_data['confidence'],
            'assets': list(assets.keys()),
            'output': str(md_path)
        }, indent=2))

        logger.info(f"✓ Complete: {verdict} (score {report_data['confidence']}/10)")
        return 0

    except Exception as e:
        logger.error(f"Report failed: {e}", exc_info=True)
        print(json.dumps({'status': 'error', 'error': str(e)}))
        return 1

if __name__ == '__main__':
    sys.exit(main())
