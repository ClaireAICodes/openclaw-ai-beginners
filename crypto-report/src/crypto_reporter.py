#!/usr/bin/env python3
"""
Standalone Daily Cryptocurrency Report Generator

Fetches data from free public APIs and generates a comprehensive report
covering fundamentals, technicals, sentiment, risks, and verdict.
"""

import sys
import os
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import time
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean
from xml.etree import ElementTree as ET

# ============== Config & Paths ==============

WORKSPACE = Path('/home/node/.openclaw/workspace')
CRYPTO_DIR = WORKSPACE / 'crypto-report'
CONFIG_PATH = CRYPTO_DIR / 'config.json'
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

# ============== HTTP Helpers ==============

def fetch_json(url: str, timeout: int = 15, max_retries: int = 2, base_delay: float = 1.0) -> Any:
    """Fetch JSON with exponential backoff retry on rate limits (429) and network errors"""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'OpenClaw-CryptoReporter/1.0 (+https://github.com/openclaw)'}
    )

    for attempt in range(max_retries):
        try:
            logger.debug(f"GET {url} (attempt {attempt + 1}/{max_retries})")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 429:
                    raise urllib.error.HTTPError(req.full_url, 429, "Rate Limited", resp.headers, None)
                content = resp.read().decode('utf-8')
                if not content.strip():
                    logger.warning(f"Empty response from {url}")
                    return {}
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

def get_coin_ohlc(coin_id: str, days: int = 7) -> List[List[float]]:
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    return fetch_json(url)

def get_fear_greed() -> Dict[str, Any]:
    data = fetch_json("https://api.alternative.me/fng/?limit=1")
    return data['data'][0] if data.get('data') else {}

def get_btc_onchain() -> Dict[str, Any]:
    """Fetch Bitcoin on-chain metrics. Try blockchain.info first, then Blockchair, then CoinGecko."""
    result = {}
    block_height = None

    # Primary: blockchain.info (usually allows CORS)
    try:
        data = fetch_json("https://blockchain.info/stats?cors=true")
        if data and isinstance(data, dict):
            # blockchain.info uses 'hash_rate' (TH/s) or 'hash_rate_terahash_per_second'
            hash_rate = data.get('hash_rate') or data.get('hash_rate_terahash_per_second')
            if hash_rate:
                result['hash_rate'] = hash_rate
            block_height = data.get('totalbc')  # total blocks
    except Exception as e:
        logger.warning(f"blockchain.info failed: {e}")

    # Secondary: Blockchair (returns difficulty, compute hash rate)
    if not result.get('hash_rate'):
        try:
            data = fetch_json("https://api.blockchair.com/bitcoin/stats")
            if data and isinstance(data, dict):
                d = data.get('data', {})
                difficulty = d.get('difficulty')
                if difficulty:
                    hash_rate = (difficulty * (2**32)) / 600 / 1e12
                    result['hash_rate'] = hash_rate
                    result['difficulty'] = difficulty
                if block_height is None:  # if not already set from blockchain.info
                    block_height = d.get('blocks')
                # Miner revenue metrics (USD)
                inflation_usd = d.get('inflation_usd_24h')  # new BTC minted value
                fees_usd = d.get('mempool_total_fee_usd')  # 24h total fees
                if inflation_usd is not None and fees_usd is not None:
                    result['miner_revenue_usd'] = inflation_usd + fees_usd
                    result['miner_reward_usd'] = inflation_usd
                    result['total_fees_usd'] = fees_usd
        except Exception as e:
            logger.warning(f"Blockchair failed: {e}")

    # Tertiary: CoinGecko includes some on-chain in coin details (no hash rate here, just fallback for block time)
    if not result.get('hash_rate'):
        try:
            data = fetch_json("https://api.coingecko.com/api/v3/coins/bitcoin")
            if data.get('block_time_in_minutes'):
                result['block_time'] = data['block_time_in_minutes']
        except Exception as e:
            logger.warning(f"CoinGecko coin details failed: {e}")

    # Compute halving info if we have block_height
    if block_height:
        # Known past halvings: {block_height: date_str}
        known_halvings = {
            210000: "2012-11-28",
            420000: "2016-07-09",
            630000: "2020-05-11",
            840000: "2024-04-20"
        }
        # Find the most recent past halving
        past = [h for h in known_halvings.keys() if h <= block_height]
        if past:
            last_halving_block = max(past)
            last_halving_date_str = known_halvings[last_halving_block]
            result['halving_last'] = last_halving_date_str
            # Compute days since last halving
            try:
                last_dt = datetime.strptime(last_halving_date_str, '%Y-%m-%d')
                days_since = (datetime.utcnow() - last_dt).days
                result['halving_days_since'] = days_since
            except Exception:
                pass  # ignore date math errors
        # Compute next halving estimate
        interval = 210000
        next_halving_height = ((block_height // interval) + 1) * interval
        blocks_until = next_halving_height - block_height
        if blocks_until > 0:
            # 10 minutes per block = 600 seconds
            estimated_seconds = blocks_until * 600
            estimated_date = datetime.utcnow() + timedelta(seconds=estimated_seconds)
            result['halving_next_estimate'] = estimated_date.strftime('%Y-%m-%d (estimated)')
            # Compute days until next halving
            days_until = (estimated_date - datetime.utcnow()).days
            result['halving_days_until'] = days_until

    return result


def get_price_series(coin_id: str, days: int = 90, interval: str = 'daily') -> List[float]:
    """Fetch closing prices from CoinGecko market_chart endpoint."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval={interval}"
    data = fetch_json(url)
    if not data or 'prices' not in data:
        return []
    return [p[1] for p in data['prices']]

def get_btc_long_term_closes(limit: int = 2000) -> List[float]:
    """Fetch up to 2000 days of BTC daily closes from CryptoCompare (free, no key)."""
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&limit={limit}"
    data = fetch_json(url)
    if not data or data.get('Response') != 'Success':
        return []
    hist = data.get('Data', {}).get('Data', [])
    # Extract closing prices; hist is sorted oldest -> newest
    closes = [float(point['close']) for point in hist if 'close' in point]
    return closes


def get_daily_volumes(coin_id: str, days: int = 30) -> List[float]:
    """Fetch daily volumes from CoinGecko market_chart endpoint."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    data = fetch_json(url)
    if not data or 'total_volumes' not in data:
        return []
    # total_volumes is list of [timestamp, volume]
    return [v[1] for v in data['total_volumes']]

def get_news_items(feeds: List[str], per_feed: int = 10) -> List[Dict[str, str]]:
    items = []
    for feed in feeds:
        feed_items = fetch_rss(feed, max_items=per_feed)
        source = urllib.parse.urlparse(feed).netloc
        for item in feed_items:
            item['source'] = source
        items.extend(feed_items)
    return items

# Mapping from ticker symbols to CoinGecko IDs
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

# ============== Analytics ==============

def calc_rsi(data: List, period: int = 14) -> Optional[float]:
    """Calculate RSI using Wilder's smoothing. Accepts either OHLC list or list of closing prices."""
    if isinstance(data[0], list) and len(data[0]) >= 5:
        closes = [c[4] for c in data]
    else:
        closes = data
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = mean(gains[:period])
    avg_loss = mean(losses[:period])
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def calc_ema(data: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average."""
    if len(data) < period:
        return None
    multiplier = 2.0 / (period + 1)
    ema = mean(data[:period])
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    return round(ema, 2)

def calc_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
    """
    Calculate Percentage Price Oscillator (PPO) and signal/histogram.
    PPO = (EMA_fast - EMA_slow) / EMA_slow * 100
    Returns normalized values, easier for scoring and comparison across price levels.
    """
    if len(closes) < slow:
        return {'macd': None, 'signal': None, 'histogram': None}

    n = len(closes)
    # EMA fast series
    ema_fast = [None] * n
    mult_f = 2.0 / (fast + 1)
    seed_f = mean(closes[:fast])
    for i in range(fast - 1, n):
        if i == fast - 1:
            ema_fast[i] = seed_f
        else:
            ema_fast[i] = (closes[i] - ema_fast[i-1]) * mult_f + ema_fast[i-1]

    # EMA slow series
    ema_slow = [None] * n
    mult_s = 2.0 / (slow + 1)
    seed_s = mean(closes[:slow])
    for i in range(slow - 1, n):
        if i == slow - 1:
            ema_slow[i] = seed_s
        else:
            ema_slow[i] = (closes[i] - ema_slow[i-1]) * mult_s + ema_slow[i-1]

    # PPO series = (EMA_fast - EMA_slow) / EMA_slow * 100
    ppo_series = []
    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None and ema_slow[i] != 0:
            ppo = round(((ema_fast[i] - ema_slow[i]) / ema_slow[i]) * 100, 2)
            ppo_series.append(ppo)
        else:
            ppo_series.append(None)

    latest_ppo = ppo_series[-1] if ppo_series[-1] is not None else None

    # Signal line: EMA of the PPO series (ignore None)
    valid_series = [v for v in ppo_series if v is not None]
    signal_line = calc_ema(valid_series, signal) if len(valid_series) >= signal else None

    histogram = round(latest_ppo - signal_line, 2) if (latest_ppo is not None and signal_line is not None) else None

    # Note: keys 'macd', 'signal', 'histogram' kept for backward compatibility; now contain PPO values.
    return {'macd': latest_ppo, 'signal': signal_line, 'histogram': histogram}

def analyze_news_sentiment(news: List[Dict[str, str]]) -> tuple[float, List[str], List[str]]:
    pos_words = ['bullish','rally','surge','gain','up','rise','growth','adoption','breakthrough','partnership','launch','success','strong','high','institutional','ETF','approval','lift','uptrend']
    neg_words = ['bearish','crash','drop','fall','down','decline','loss','sell-off','regulation','sec','lawsuit','hack','scam','fraud','exploit','ban','warning','risk','trouble','low','weak','concern']

    text = " ".join([n['title'] + " " + n.get('description','') for n in news]).lower()
    pos = [w for w in pos_words if w in text]
    neg = [w for w in neg_words if w in text]

    pos_count = len(pos)
    neg_count = len(neg)
    total = pos_count + neg_count
    score = (pos_count - neg_count) / total if total > 0 else 0.0
    return round(score, 3), pos[:5], neg[:5]

def assess_risk(
    news_sent: tuple,
    btc_dom: Optional[float],
    btc_price: Optional[float] = None,
    wma_200: Optional[float] = None
) -> tuple[float, List[str], List[tuple]]:
    score = 0.0
    factors = []
    contributions = []  # (label, added_score)
    sent_score, _, neg_kws = news_sent

    if sent_score <= -0.3:
        add = 0.2
        score += add
        factors.append("Negative news sentiment")
        contributions.append(("Negative news sentiment", add, f"sent_score={sent_score:.3f}"))
    if len(neg_kws) >= 5:
        add = 0.1
        score += add
        factors.append("Multiple negative keywords")
        contributions.append(("Multiple negative keywords", add, f"count={len(neg_kws)}"))
    if any(k in " ".join(neg_kws) for k in ['regulation','sec','lawsuit','ban','compliance']):
        add = 0.2
        score += add
        factors.append("Regulatory concerns")
        contributions.append(("Regulatory concerns", add, "keywords detected"))
    if btc_dom and btc_dom > 60:
        add = 0.15
        score += add
        factors.append(f"High BTC dominance ({btc_dom:.1f}%)")
        contributions.append(("High BTC dominance", add, f"{btc_dom:.1f}%"))

    # 200-week Moving Average risk factor: being far above adds risk
    wma200_dist = None
    if btc_price is not None and wma_200 is not None and wma_200 > 0:
        distance_pct = (btc_price - wma_200) / wma_200 * 100
        wma200_dist = distance_pct
        if distance_pct > 100:
            add = 0.5
            score += add
            factors.append(f"Price >100% above WMA200")
            contributions.append(("WMA200 premium", add, f"+{distance_pct:.1f}%"))
        elif distance_pct > 50:
            add = 0.3
            score += add
            factors.append(f"Price >50% above WMA200")
            contributions.append(("WMA200 premium", add, f"+{distance_pct:.1f}%"))
        elif distance_pct > 30:
            add = 0.2
            score += add
            factors.append(f"Price >30% above WMA200")
            contributions.append(("WMA200 premium", add, f"+{distance_pct:.1f}%"))

    return min(1.0, score), factors, contributions, wma200_dist

def compute_technical_score(
    rsi: Optional[float],
    trend: int,
    fng: int,
    ppo_hist: Optional[float] = None,
    volume_ratio: Optional[float] = None
) -> tuple[float, str]:
    """
    Compute technical score (0-10) from multiple signals.

    Components (base 5.0, max swing ±5.0):
    - RSI: ±1.0 (<30 oversold, >70 overbought)
    - SMA30 Trend: ±1.0 (price above/below)
    - PPO Histogram: ±1.5 scaled by magnitude (max at |hist|>=2%)
    - Volume Confirmation: ±0.5 directional (high vol confirms trend, low vol penalizes)
    - Fear & Greed: +1.0 (fear) / -1.5 (greed)

    Returns (score, reasons_string)
    """
    score = 5.0
    reasons = []

    # RSI (±1.0)
    if rsi is not None:
        if rsi < 30:
            score += 1.0
            reasons.append(f"RSI oversold ({rsi})")
        elif rsi > 70:
            score -= 1.0
            reasons.append(f"RSI overbought ({rsi})")
        else:
            reasons.append(f"RSI neutral ({rsi})")

    # SMA30 trend (±1.0)
    if trend > 0:
        score += 1.0
        reasons.append("Price > SMA30")
    elif trend < 0:
        score -= 1.0
        reasons.append("Price < SMA30")

    # PPO histogram (±1.5, scaled by magnitude)
    if ppo_hist is not None:
        if ppo_hist > 0:
            points = min(1.5, 1.5 * min(abs(ppo_hist) / 2.0, 1.0))
            score += points
            reasons.append(f"PPO histogram +{ppo_hist:.2f}%")
        elif ppo_hist < 0:
            points = min(1.5, 1.5 * min(abs(ppo_hist) / 2.0, 1.0))
            score -= points
            reasons.append(f"PPO histogram {ppo_hist:.2f}%")

    # Volume confirmation (±0.5, directional)
    if volume_ratio is not None:
        if volume_ratio > 1.5:
            if trend > 0:
                score += 0.5
                reasons.append(f"Volume {volume_ratio:.1f}× MA (confirms uptrend)")
            elif trend < 0:
                score -= 0.5
                reasons.append(f"Volume {volume_ratio:.1f}× MA (confirms downtrend)")
        elif volume_ratio < 0.5:
            score -= 0.5
            reasons.append(f"Volume {volume_ratio:.1f}× MA (weak conviction)")

    # Fear & Greed (+1.0 / -1.5)
    if fng <= 25:
        score += 1.0
        reasons.append("Extreme fear (contrarian)")
    elif fng >= 75:
        score -= 1.5
        reasons.append("Extreme greed (contrarian)")

    return max(0.0, min(10.0, score)), "; ".join(reasons)

def compute_fundamentals_score(onchain: Dict[str, Any]) -> float:
    """
    Weighted score (0-10) based on:
    - Halving cycle phase (35%)
    - Difficulty trend - 2w change % (35%)
    - Hash rate momentum - 24h change % (15%)
    - Miner revenue momentum - 24h change % (15%)
    """
    # 1) Halving phase (days_since)
    days_since = onchain.get('halving_days_since')
    if days_since is not None:
        if days_since < 300:
            s_halving = 9.0
        elif days_since < 550:
            s_halving = 7.0
        elif days_since < 800:
            s_halving = 4.0   # distribution/transition, somewhat bearish
        else:
            s_halving = 2.0   # deep bear
    else:
        s_halving = 5.0

    # 2) Difficulty trend (% change)
    diff_change = onchain.get('difficulty_change_pct')
    if diff_change is not None:
        s_diff = 5.0 + diff_change * 0.2
        s_diff = max(0.0, min(10.0, s_diff))
    else:
        s_diff = 5.0

    # 3) Hash rate momentum (% change)
    hr_change = onchain.get('btc_hash_rate_change_24h')
    if hr_change is not None:
        s_hr = 5.0 + hr_change * 0.4
        s_hr = max(0.0, min(10.0, s_hr))
    else:
        s_hr = 5.0

    # 4) Miner revenue momentum (% change)
    rev_change = onchain.get('miner_revenue_change_pct')
    if rev_change is not None:
        s_rev = 5.0 + rev_change * 0.2
        s_rev = max(0.0, min(10.0, s_rev))
    else:
        s_rev = 5.0

    # Weighted total
    score = (
        0.35 * s_halving +
        0.35 * s_diff +
        0.15 * s_hr +
        0.15 * s_rev
    )
    return round(score, 2)

def compute_sentiment_score(fng: int, news_sent: float) -> float:
    # FnG 0-100 -> 0-10, news -1..1 -> 0-10 (5 neutral)
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
    logger.info("Starting Crypto Reporter")
    try:
        config = json.load(open(CONFIG_PATH))
        logger.info(f"Config: assets={config['TRACKED_ASSETS']}, weights={config['VERDICT_WEIGHTS']}")

        # 1. Coin data (also provides global metrics when summed)
        logger.info("Fetching coin market data...")
        coin_ids = [COINGECKO_IDS[c] for c in config['TRACKED_ASSETS']]
        coins = get_coin_markets(coin_ids)

        # Compute tracked assets totals and BTC dominance from our coin data
        # (avoiding extra API call to prevent rate limits)
        total_mcap_tracked = sum(c.get('market_cap', 0) for c in coins if c.get('market_cap'))
        total_vol_tracked = sum(c.get('total_volume', 0) for c in coins if c.get('total_volume'))
        btc_asset = next((c for c in coins if c['symbol'].upper() == 'BTC'), None)
        btc_dom = None
        if btc_asset and total_mcap_tracked:
            btc_dom = (btc_asset.get('market_cap', 0) / total_mcap_tracked) * 100

        # Global market cap and volume are not available without extra call
        mcap = None
        vol = None
        eth_dom = None
        stable_dom = None
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

        # Fetch OHLC for BTC only (to avoid rate limits; technicals use BTC as proxy)
        # Other assets will show N/A for RSI/trend in report (acceptable given rate constraints)
        time.sleep(2)  # Rate limit mitigation
        # 2. Global market metrics (BTC/ETH/Stable dominance, total mcap/vol)
        time.sleep(2)  # Rate limit mitigation
        logger.info("Attempting to fetch global market metrics...")
        try:
            global_data = get_global_market()
            # Use market_cap_percentage for real dominance numbers
            mc_pct = global_data.get('market_cap_percentage', {})
            btc_dom_global = mc_pct.get('btc')
            eth_dom_global = mc_pct.get('eth')
            # Sum major stablecoins (USDT, USDC, BUSD, DAI, etc.)
            stable_pct = mc_pct.get('usdt', 0) + mc_pct.get('usdc', 0) + mc_pct.get('busd', 0) + mc_pct.get('dai', 0)
            mcap = global_data.get('total_market_cap', {}).get('usd')
            vol = global_data.get('total_volume', {}).get('usd')
            if btc_dom_global is not None:
                btc_dom = btc_dom_global
            if eth_dom_global is not None:
                eth_dom = eth_dom_global
            if stable_pct > 0:
                stable_dom = stable_pct
            logger.info(f"Global market data: BTC dom {btc_dom:.1f}%, ETH dom {eth_dom if eth_dom is not None else 'N/A'}%, Stablecoins {stable_dom if stable_dom is not None else 'N/A'}%")
        except Exception as e:
            logger.warning(f"Global market fetch failed: {e}. Using computed BTC dominance from tracked assets; ETH/stables will be N/A.")
            if btc_dom is None and total_mcap_tracked > 0:
                btc_asset = assets.get('BTC')
                if btc_asset:
                    btc_dom = (btc_asset.get('market_cap', 0) / total_mcap_tracked) * 100

        # 3. Fetch BTC technical data
        time.sleep(2)  # Rate limit mitigation
        if 'BTC' in assets:
            try:
                logger.info("Fetching BTC daily closes for technical indicators...")
                btc_id = COINGECKO_IDS['BTC']
                # Daily closes (90 days) for RSI, MACD, SMA30, volume
                closes_daily = get_price_series(btc_id, days=90, interval='daily')
                if not closes_daily or len(closes_daily) < 15:
                    logger.warning(f"Insufficient daily data for BTC: got {len(closes_daily) if closes_daily else 0} points")
                else:
                    btc_rsi = calc_rsi(closes_daily)
                    assets['BTC']['rsi'] = btc_rsi
                    sma_30 = mean(closes_daily[-30:]) if len(closes_daily) >= 30 else (mean(closes_daily) if closes_daily else None)
                    current = closes_daily[-1]
                    assets['BTC']['sma_30'] = sma_30
                    assets['BTC']['trend'] = 1 if (sma_30 and current > sma_30) else -1 if (sma_30 and current < sma_30) else 0
                    # MACD (12/26/9) - uses daily closes
                    macd_data = calc_macd(closes_daily)
                    assets['BTC']['macd'] = macd_data.get('macd')
                    assets['BTC']['macd_signal'] = macd_data.get('signal')
                    assets['BTC']['macd_hist'] = macd_data.get('histogram')
                    # Volume: fetch last 30 days of daily volumes and compute 30‑day MA
                    volumes = get_daily_volumes(btc_id, days=30)
                    if volumes:
                        vol_ma = mean(volumes[-30:]) if len(volumes) >= 30 else (mean(volumes) if volumes else None)
                        assets['BTC']['volume_ma'] = vol_ma
                    # 200-week Moving Average (long-term risk metric) - fetch ~2000 daily closes from CryptoCompare
                    time.sleep(2)  # additional rate limit mitigation
                    try:
                        closes_long = get_btc_long_term_closes(limit=2000)
                        # Need at least 200 weeks of data; 200 weeks ~ 1400 days
                        if closes_long and len(closes_long) >= 1400:
                            wma_200 = mean(closes_long[-1400:])
                            assets['BTC']['wma_200'] = wma_200
                            logger.info(f"WMA200 (200w): ${wma_200:,.2f}")
                        elif closes_long and len(closes_long) >= 200:
                            # Fallback: if we have at least 200 days, compute shorter average and label accordingly
                            wma_200 = mean(closes_long[-200:])
                            assets['BTC']['wma_200'] = wma_200
                            logger.info(f"WMA200 (limited): ${wma_200:,.2f} (based on {len(closes_long)} days)")
                        else:
                            logger.warning(f"Insufficient long-term data for WMA200: got {len(closes_long) if closes_long else 0} points")
                    except Exception as e:
                        logger.warning(f"Failed to fetch long-term closes for WMA200: {e}")
                    trend_str = 'up' if assets['BTC']['trend'] > 0 else 'down' if assets['BTC']['trend'] < 0 else 'flat'
                    macd_val = assets['BTC'].get('macd')
                    macd_str = f"{macd_val:.2f}" if macd_val is not None else 'N/A'
                    wma200_val = assets['BTC'].get('wma_200')
                    logger.info(f"BTC technicals: RSI={btc_rsi:.1f}, SMA30=${sma_30:,.2f}, trend={trend_str}, PPO={macd_str}" + (f", WMA200=${wma200_val:,.2f}" if wma200_val else ""))
            except Exception as e:
                logger.warning(f"Daily close fetch for BTC failed: {e}")

        # 3. Fear & Greed
        time.sleep(2)  # Rate limit mitigation
        logger.info("Fetching Fear & Greed index...")
        fng_data = get_fear_greed()
        fng_val = int(fng_data.get('value', 50))
        fng_lbl = fng_data.get('value_classification', 'Neutral')

        # 4. BTC on-chain
        time.sleep(2)  # Rate limit mitigation
        logger.info("Fetching BTC on-chain metrics...")
        btc_onchain = get_btc_onchain()
        btc_hash = btc_onchain.get('hash_rate')  # TH/s

        # 5. News
        time.sleep(2)  # Rate limit mitigation between different sources
        logger.info("Fetching news from RSS feeds...")
        feeds = config.get('NEWS_RSS_FEEDS', ['https://www.coindesk.com/arc/outboundfeeds/rss/', 'https://cointelegraph.com/rss'])
        news = get_news_items(feeds, per_feed=10)
        news_sent, pos_kw, neg_kw = analyze_news_sentiment(news)
        news_sent_0_10 = round(5 + (news_sent * 5), 2)

        # 6. Scores
        fundamentals_score = compute_fundamentals_score(btc_onchain)
        sentiment_score = compute_sentiment_score(fng_val, news_sent)

        # Technicals from BTC representative
        btc = assets.get('BTC', {})
        # Compute volume ratio (24h volume / 30-day MA)
        vol = btc.get('volume_24h')
        vol_ma = btc.get('volume_ma')
        volume_ratio = (vol / vol_ma) if (vol is not None and vol_ma is not None and vol_ma > 0) else None
        tech_score, tech_rationale = compute_technical_score(
            rsi=btc.get('rsi'),
            trend=btc.get('trend', 0),
            fng=fng_val,
            ppo_hist=btc.get('macd_hist'),
            volume_ratio=volume_ratio
        )

        # Risk assessment (needs btc price and 200W SMA)
        risk_score, risk_factors, risk_contributions, wma200_dist = assess_risk(
            (news_sent, pos_kw, neg_kw),
            btc_dom,
            btc_price=btc.get('price'),
            wma_200=btc.get('wma_200')
        )
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

        # Build report data
        report_date = datetime.now().strftime('%Y-%m-%d')

        # Track 24h hash rate change using local state file
        state_file = ARTIFACTS_DIR / 'btc_hash_state.json'
        prev_hash_rate = None
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                prev_hash_rate = state.get('hash_rate')
            except Exception as e:
                logger.warning(f"Failed to read hash rate state: {e}")

        hash_rate_change_24h = None
        if btc_hash is not None and prev_hash_rate is not None and prev_hash_rate > 0:
            hash_rate_change_24h = (btc_hash - prev_hash_rate) / prev_hash_rate * 100

        # Save current state for next day
        if btc_hash is not None:
            try:
                state = {'date': report_date, 'hash_rate': btc_hash}
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write hash rate state: {e}")

        # Track difficulty change over ~2 weeks (retarget period)
        difficulty_state_file = ARTIFACTS_DIR / 'btc_difficulty_state.json'
        prev_difficulty = None
        if difficulty_state_file.exists():
            try:
                with open(difficulty_state_file) as f:
                    state = json.load(f)
                prev_difficulty = state.get('difficulty')
            except Exception as e:
                logger.warning(f"Failed to read difficulty state: {e}")

        difficulty_change_pct = None
        current_difficulty = btc_onchain.get('difficulty')
        if current_difficulty is not None and prev_difficulty is not None and prev_difficulty > 0:
            difficulty_change_pct = (current_difficulty - prev_difficulty) / prev_difficulty * 100

        # Save current difficulty for next comparison
        if current_difficulty is not None:
            try:
                state = {'date': report_date, 'difficulty': current_difficulty}
                with open(difficulty_state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write difficulty state: {e}")

        # Track miner revenue change (24h)
        miner_rev_state_file = ARTIFACTS_DIR / 'btc_miner_rev_state.json'
        prev_miner_rev = None
        if miner_rev_state_file.exists():
            try:
                with open(miner_rev_state_file) as f:
                    state = json.load(f)
                prev_miner_rev = state.get('miner_revenue_usd')
            except Exception as e:
                logger.warning(f"Failed to read miner revenue state: {e}")

        miner_rev_change_pct = None
        current_miner_rev = btc_onchain.get('miner_revenue_usd')
        if current_miner_rev is not None and prev_miner_rev is not None and prev_miner_rev > 0:
            miner_rev_change_pct = (current_miner_rev - prev_miner_rev) / prev_miner_rev * 100

        # Save current miner revenue for next comparison
        if current_miner_rev is not None:
            try:
                state = {'date': report_date, 'miner_revenue_usd': current_miner_rev}
                with open(miner_rev_state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write miner revenue state: {e}")

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
                'btc_dominance': btc_dom,
                'fear_greed': {'value': fng_val, 'label': fng_lbl}
            },
            'assets': assets,
            'news': {
                'count': len(news),
                'sentiment_score': news_sent,
                'positive_keywords': pos_kw,
                'negative_keywords': neg_kw,
                'items': news[:5]  # top 5 most recent
            },
            'risks': {
                'score': risk_score,
                'factors': risk_factors
            },
            'onchain': {
                'btc_hash_rate': btc_hash,
                'btc_hash_rate_change_24h': hash_rate_change_24h,
                'halving_last': btc_onchain.get('halving_last'),
                'halving_next_estimate': btc_onchain.get('halving_next_estimate'),
                'halving_days_since': btc_onchain.get('halving_days_since'),
                'halving_days_until': btc_onchain.get('halving_days_until'),
                'difficulty': current_difficulty,
                'difficulty_change_pct': difficulty_change_pct,
                'miner_revenue_usd': btc_onchain.get('miner_revenue_usd'),
                'miner_revenue_change_pct': miner_rev_change_pct,
                'total_fees_usd': btc_onchain.get('total_fees_usd'),
                'miner_reward_usd': btc_onchain.get('miner_reward_usd')
            }
        }

        # 8. Format markdown
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

        # Highlights
        if mcap:
            markdown_lines.append(f"- **Global Market Cap:** ${mcap:,.0f}")
        if vol:
            markdown_lines.append(f"- **24h Volume:** ${vol:,.0f}")
        if btc_dom:
            markdown_lines.append(f"- **BTC Dominance:** {btc_dom:.1f}%")
        if eth_dom:
            markdown_lines.append(f"- **ETH Dominance:** {eth_dom:.1f}%")
        if stable_dom:
            markdown_lines.append(f"- **Stablecoin Dominance:** {stable_dom:.1f}%")
        markdown_lines.append(f"- **Fear & Greed:** {fng_val} ({fng_lbl})")
        # Add BTC hash rate 24h change if available
        hash_change = report_data['onchain'].get('btc_hash_rate_change_24h')
        if hash_change is not None:
            markdown_lines.append(f"- **BTC Hash Rate 24h:** {hash_change:+.2f}%")
        markdown_lines.append(f"- **Assets analyzed:** {', '.join(config['TRACKED_ASSETS'])}")
        markdown_lines.extend(["", "## Score Breakdown", "", "| Dimension | Score | Weight | Weighted |", "|-----------|-------|--------|----------|"])

        weights = w
        s = report_data['scores']
        for dim in ['fundamentals', 'technicals', 'sentiment', 'risks_adjusted']:
            w_val = weights.get(dim.split('_')[0], 0.25)  # map risks_adjusted -> risks
            weighted_val = s[dim] * w_val
            markdown_lines.append(f"| {dim.capitalize()} | {s[dim]}/10 | {w_val:.0%} | {weighted_val:.2f} |")
        markdown_lines.append(f"| **Total** | | **100%** | **{s['weighted_total']:.2f}** |")

        # Asset table
        markdown_lines.extend(["", "## Asset Analysis", "", "| Symbol | Name | Price | 24h Change |", "|--------|------|-------|------------|"])
        for sym, a in assets.items():
            price = f"${a['price']:,.2f}" if a.get('price') else "N/A"
            change = f"{a.get('change_24h', 0):+.2f}%" if a.get('change_24h') is not None else "N/A"
            markdown_lines.append(f"| {sym} | {a['name']} | {price} | {change} |")

        # Fundamentals
        # BTC Technical Indicators section
        btc_tech = assets.get('BTC', {})
        rsi_val = btc_tech.get('rsi')
        sma_val = btc_tech.get('sma_30')
        wma200_val = btc_tech.get('wma_200')
        trend_val = btc_tech.get('trend', 0)
        macd_val = btc_tech.get('macd')
        macd_sig = btc_tech.get('macd_signal')
        macd_hist = btc_tech.get('macd_hist')
        markdown_lines.append("")
        markdown_lines.append("## BTC Technical Indicators (Daily)")
        markdown_lines.append("")
        if rsi_val is not None:
            markdown_lines.append(f"- **RSI:** {rsi_val:.1f}")
        else:
            markdown_lines.append("- **RSI:** N/A")
        if sma_val is not None:
            markdown_lines.append(f"- **SMA30:** ${sma_val:,.2f}")
        else:
            markdown_lines.append("- **SMA30:** N/A")
        if wma200_val is not None:
            markdown_lines.append(f"- **WMA200:** ${wma200_val:,.2f}")
        else:
            markdown_lines.append("- **WMA200:** N/A")
        trend_str = "> SMA30" if trend_val > 0 else "< SMA30" if trend_val < 0 else "Flat"
        markdown_lines.append(f"- **Trend:** {trend_str}")

        # 24h price change and volume (from latest market data)
        btc_price = btc_tech.get('price')
        btc_change = btc_tech.get('change_24h')
        btc_vol = btc_tech.get('volume_24h')
        btc_vol_ma = btc_tech.get('volume_ma')
        if btc_change is not None:
            change_str = f"{btc_change:+.2f}%"
            markdown_lines.append(f"- **24h Change:** {change_str}")
        if btc_vol is not None:
            markdown_lines.append(f"- **24h Volume:** ${btc_vol:,.0f}")
        if btc_vol_ma is not None:
            markdown_lines.append(f"- **Volume MA(30):** ${btc_vol_ma:,.0f}")

        if macd_val is not None:
            markdown_lines.append(f"- **PPO:** {macd_val:+.2f}%")
            if macd_sig is not None:
                markdown_lines.append(f"- **PPO Signal:** {macd_sig:+.2f}%")
            if macd_hist is not None:
                markdown_lines.append(f"- **PPO Histogram:** {macd_hist:+.2f}%")

        # Generate brief analysis of BTC technicals
        analysis = []
        if rsi_val is not None:
            if rsi_val < 30:
                analysis.append("RSI indicates oversold conditions, potential bullish reversal")
            elif rsi_val > 70:
                analysis.append("RSI indicates overbought conditions, potential bearish reversal")
            else:
                analysis.append("RSI is neutral")
        if macd_hist is not None:
            if macd_hist > 0:
                analysis.append("PPO above signal suggests bullish momentum")
            else:
                analysis.append("PPO below signal indicates bearish momentum")
        if trend_val > 0:
            analysis.append("Price above 30‑day SMA confirms uptrend")
        elif trend_val < 0:
            analysis.append("Price below 30‑day SMA confirms downtrend")
        else:
            analysis.append("Price is testing SMA")
        if btc_vol is not None and btc_vol_ma is not None:
            if btc_vol > btc_vol_ma * 1.2:
                analysis.append("Current volume is significantly above average, strengthening the signal")
        if analysis:
            markdown_lines.append("**Analysis:** " + "; ".join(analysis) + ".")



        markdown_lines.extend(["", "## Fundamentals Overview", ""])
        if btc_hash:
            change_str = f" (24h change: {hash_rate_change_24h:+.2f}%)" if hash_rate_change_24h is not None else ""
            markdown_lines.append(f"- **BTC Hash Rate:** {btc_hash:,.0f} TH/s{change_str}")
        else:
            markdown_lines.append("- **BTC Hash Rate:** Data unavailable")
        # Add halving dates
        halving_last = report_data.get('onchain', {}).get('halving_last')
        halving_next = report_data.get('onchain', {}).get('halving_next_estimate')
        halving_days_since = report_data.get('onchain', {}).get('halving_days_since')
        halving_days_until = report_data.get('onchain', {}).get('halving_days_until')
        if halving_last:
            if halving_days_since is not None:
                markdown_lines.append(f"- **Last BTC Halving:** {halving_last} ({halving_days_since} days ago)")
            else:
                markdown_lines.append(f"- **Last BTC Halving:** {halving_last}")
        if halving_next:
            if halving_days_until is not None:
                markdown_lines.append(f"- **Next BTC Halving (Estimated):** {halving_next} — in {halving_days_until} days")
            else:
                markdown_lines.append(f"- **Next BTC Halving (Estimated):** {halving_next}")
        # Add halving cycle phase interpretation
        if halving_days_since is not None:
            ds = halving_days_since
            if ds < 300:
                phase = "Early Post-Halving (Bullish Phase)"
            elif ds < 550:
                phase = "Mid Post-Halving (Peak Bullish)"
            else:
                phase = "Late Post-Halving (Distribution/Bear Risk)"
            markdown_lines.append(f"- **Halving Cycle Phase:** {phase}")
        # Add miner revenue and difficulty metrics
        miner_rev = report_data.get('onchain', {}).get('miner_revenue_usd')
        miner_rev_change = report_data.get('onchain', {}).get('miner_revenue_change_pct')
        fees = report_data.get('onchain', {}).get('total_fees_usd')
        diff = report_data.get('onchain', {}).get('difficulty')
        diff_change = report_data.get('onchain', {}).get('difficulty_change_pct')
        if miner_rev is not None:
            rev_str = f"${miner_rev:,.0f}"
            if miner_rev_change is not None:
                rev_str += f" (24h change: {miner_rev_change:+.2f}%)"
            if fees is not None and fees > 0:
                fee_pct = (fees / miner_rev) * 100
                markdown_lines.append(f"- **Miner Revenue (24h):** {rev_str} (fees: ${fees:,.0f}, {fee_pct:.1f}% of revenue)")
            else:
                markdown_lines.append(f"- **Miner Revenue (24h):** {rev_str}")
        if diff is not None:
            diff_str = f"{diff:,.0f}"
            if diff_change is not None:
                diff_str += f" (2w change: {diff_change:+.2f}%)"
            markdown_lines.append(f"- **Network Difficulty:** {diff_str}")
        markdown_lines.append("- *More detailed on-chain metrics require premium data sources*")

        # Sentiment
        markdown_lines.extend(["", "## Sentiment Analysis", ""])
        markdown_lines.append(f"- **Fear & Greed Index:** {fng_val} ({fng_lbl})")
        markdown_lines.append(f"- **News Sentiment Score:** {news_sent:.3f} (-1 to +1)")
        markdown_lines.append(f"  - Positive keywords: {', '.join(pos_kw) if pos_kw else 'None'}")
        markdown_lines.append(f"  - Negative keywords: {', '.join(neg_kw) if neg_kw else 'None'}")

        # Top news stories
        top_news = report_data.get('news', {}).get('items', [])
        if top_news:
            markdown_lines.extend(["", "## Top Headlines", ""])
            for item in top_news:
                title = item.get('title', 'No title')
                link = item.get('link', '#')
                source = item.get('source', 'Unknown')
                markdown_lines.append(f"- [{title}]({link}) — {source}")

        # Risks - more informative formatting
        markdown_lines.extend(["", "## Risk Assessment", ""])
        markdown_lines.append(f"**Overall Risk Score:** {risk_score:.3f} / 1.0")
        markdown_lines.append(f"**Adjusted Score (inverted):** {risks_adj_score:.1f} / 10.0")
        markdown_lines.append("")
        if risk_contributions:
            markdown_lines.append("**Factor Breakdown:**")
            for label, add, detail in risk_contributions:
                markdown_lines.append(f"- {label}: +{add:.2f} ({detail})")
            markdown_lines.append("")
            # Show summary with total risk score
            markdown_lines.append(f"**Total Risk Factors:** {len(risk_contributions)} contributing {risk_score:.3f} points.")
        else:
            markdown_lines.append("**No significant risk factors detected.**")
            markdown_lines.append(f"Raw risk score: {risk_score:.3f} → Adjusted: {risks_adj_score:.1f}/10")
        # Add contextual market risk indicators
        markdown_lines.append("")
        markdown_lines.append("**Context:**")
        markdown_lines.append(f"- News sentiment score: {news_sent:.3f} (-1 to +1)")
        if btc_dom:
            markdown_lines.append(f"- BTC dominance: {btc_dom:.1f}%")
        if wma200_dist is not None:
            markdown_lines.append(f"- BTC price vs WMA200: {wma200_dist:+.1f}%")

        # Rationale
        markdown_lines.extend(["", "## Verdict Rationale", "", f"The **{verdict}** recommendation is based on a weighted composite score of **{report_data['confidence']}/10**."])
        markdown_lines.append("")
        markdown_lines.append(f"- **Technical factors:** {tech_rationale}.")
        markdown_lines.append(f"- **Sentiment:** Fear & Greed at {fng_val} ({fng_lbl}).")
        markdown_lines.append(f"- **News tone:** {'Positive' if news_sent > 0.1 else 'Negative' if news_sent < -0.1 else 'Neutral'}.")
        markdown_lines.append(f"- **Risk factors:** {len(risk_factors)} identified: {'; '.join(risk_factors) if risk_factors else 'Minimal'}.")

        # Methodology
        markdown_lines.extend(["", "## Methodology Notes", "",
            "- Data sources: CoinGecko API, Alternative.me, Blockchair, RSS news feeds.",
            "- Technical indicators: RSI (14-day), 30-day SMA, PPO (12/26/9), 30-day Volume MA.",
            "- Technical score: weighted combination of RSI, trend, PPO histogram, volume confirmation, and Fear & Greed (0-10 scale).",
            "- Sentiment: Simple keyword-based analysis of recent news headlines.",
            "- Risk assessment: Aggregates negative news keywords, regulatory mentions, BTC dominance.",
            "- **Not financial advice** - for informational purposes only.",
            "",
            f"*Generated by Crypto Reporter v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*"
        ])

        markdown = "\n".join(markdown_lines)

        # 9. Save
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

        # Send email notification if enabled
        if config.get('ENABLE_EMAIL_NOTIFICATIONS'):
            try:
                email_recipient = config.get('EMAIL_RECIPIENT')
                subject_prefix = config.get('EMAIL_SUBJECT_PREFIX', 'Crypto Report')
                subject = f"{subject_prefix}: {verdict} (Score: {report_data['confidence']}/10) - {date_str}"

                # Extract data
                mcap_usd = global_data.get('total_market_cap', {}).get('usd', 0)
                vol_usd = global_data.get('total_volume', {}).get('usd', 0)
                s = report_data['scores']
                weights = config['VERDICT_WEIGHTS']
                risks = report_data.get('risks', {})
                risk_factors = risks.get('factors', [])
                risk_score = risks.get('score', 0)
                wma200_dist = report_data.get('wma200_dist')
                risks_adj_score = report_data.get('risks_adjusted', 10.0 - (risk_score * 10))
                news_items = report_data.get('news', {}).get('items', [])
                news_sent = report_data.get('news', {}).get('sentiment_score', 0)
                pos_kw = report_data.get('news', {}).get('positive_keywords', [])
                neg_kw = report_data.get('news', {}).get('negative_keywords', [])

                # Precompute BTC tech display values (safe for None)
                rsi_val = btc_tech.get('rsi')
                rsi_display = f"{rsi_val:.1f}" if rsi_val is not None else "N/A"
                rsi_status = "Oversold" if rsi_val is not None and rsi_val < 30 else "Overbought" if rsi_val is not None and rsi_val > 70 else "Neutral"
                sma30_val = btc_tech.get('sma_30')
                sma30_display = f"${sma30_val:,.2f}" if sma30_val is not None else "N/A"
                wma200_val = btc_tech.get('wma_200')
                wma200_display = f"${wma200_val:,.2f}" if wma200_val is not None else "N/A"
                trend_val = btc_tech.get('trend', 0)
                trend_display = "> SMA30" if trend_val > 0 else "< SMA30" if trend_val < 0 else "Flat"
                trend_status = "Bullish" if trend_val > 0 else "Bearish" if trend_val < 0 else "Neutral"
                ppo_hist = btc_tech.get('macd_hist')
                ppo_display = f"{ppo_hist:+.2f}%" if ppo_hist is not None else "N/A"
                btc_price_val = btc_tech.get('price', 0)
                btc_change_val = btc_tech.get('change_24h', 0)
                btc_vol_val = btc_tech.get('volume_24h', 0)
                btc_vol_ma_val = btc_tech.get('volume_ma')

                # Build comprehensive HTML email
                html_lines = [
                    '<!DOCTYPE html>',
                    '<html>',
                    '<head>',
                    '  <style>',
                    '    body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }',
                    '    .header { background: linear-gradient(135deg, #4a90e2, #357abd); color: #1a1a1a; padding: 25px; border-radius: 10px; margin-bottom: 25px; text-align: center; }',
                    '    .verdict { font-size: 28px; font-weight: bold; margin: 10px 0; }',
                    '    .score { font-size: 20px; opacity: 0.9; }',
                    '    .section { margin: 25px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; border-left: 4px solid #4a90e2; }',
                    '    .section h2 { color: #4a90e2; margin-top: 0; border-bottom: 2px solid #4a90e2; padding-bottom: 8px; }',
                    '    table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }',
                    '    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }',
                    '    th { background-color: #4a90e2; color: white; font-weight: bold; }',
                    '    .positive { color: #28a745; font-weight: bold; }',
                    '    .negative { color: #dc3545; font-weight: bold; }',
                    '    .neutral { color: #6c757d; }',
                    '    .highlights { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }',
                    '    .highlight { background: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }',
                    '    .highlight strong { color: #4a90e2; }',
                    '    .breakdown-table th { text-align: center; }',
                    '    .breakdown-table .weighted { text-align: right; }',
                    '    a { color: #4a90e2; text-decoration: none; }',
                    '    a:hover { text-decoration: underline; }',
                    '    .disclaimer { font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px; }',
                    '    .news-item { margin: 10px 0; padding: 10px; background: white; border-left: 3px solid #4a90e2; }',
                    '    .news-title { font-weight: bold; }',
                    '    .news-source { color: #666; font-size: 12px; margin-left: 10px; }',
                    '  </style>',
                    '</head>',
                    '<body>',
                    f'  <div class="header">',
                    f'    <h1>📊 Daily Cryptocurrency Market Report</h1>',
                    f'    <div class="verdict">Market Verdict: {verdict}</div>',
                    f'    <div class="score">Confidence Score: {report_data["confidence"]}/10</div>',
                    f'    <div>Report Date: {date_str}</div>',
                    '  </div>',
                    '',
                    '  <div class="section">',
                    '    <h2>📈 Key Highlights</h2>',
                    '    <div class="highlights">',
                    f'      <div class="highlight"><strong>Global Market Cap:</strong><br>${mcap_usd:,.0f}</div>',
                    f'      <div class="highlight"><strong>24h Volume:</strong><br>${vol_usd:,.0f}</div>',
                    f'      <div class="highlight"><strong>BTC Dominance:</strong><br>{btc_dom:.1f}%</div>',
                    f'      <div class="highlight"><strong>ETH Dominance:</strong><br>{eth_dom:.1f}%</div>' if eth_dom is not None else '      <div class="highlight"><strong>ETH Dominance:</strong><br>N/A</div>',
                    f'      <div class="highlight"><strong>Stablecoin Dom:</strong><br>{stable_dom:.1f}%</div>' if stable_dom is not None else '      <div class="highlight"><strong>Stablecoin Dom:</strong><br>N/A</div>',
                    f'      <div class="highlight"><strong>Fear & Greed:</strong><br>{fng_val} ({fng_lbl})</div>',
                    '    </div>',
                    '  </div>',
                    '',
                    '  <div class="section">',
                    '    <h2>📊 Score Breakdown</h2>',
                    '    <table class="breakdown-table">',
                    '      <tr><th>Dimension</th><th>Score</th><th>Weight</th><th>Weighted</th></tr>',
                    f'      <tr><td>Fundamentals</td><td>{s["fundamentals"]}/10</td><td>30%</td><td class="weighted">{weights.get("fundamentals",0.3)*s["fundamentals"]:.2f}</td></tr>',
                    f'      <tr><td>Technicals</td><td>{s["technicals"]}/10</td><td>25%</td><td class="weighted">{weights.get("technicals",0.25)*s["technicals"]:.2f}</td></tr>',
                    f'      <tr><td>Sentiment</td><td>{s["sentiment"]}/10</td><td>20%</td><td class="weighted">{weights.get("sentiment",0.2)*s["sentiment"]:.2f}</td></tr>',
                    f'      <tr><td>Risks (adj)</td><td>{s["risks_adjusted"]}/10</td><td>25%</td><td class="weighted">{weights.get("risks",0.25)*s["risks_adjusted"]:.2f}</td></tr>',
                    f'      <tr><td colspan="3"><strong>Total</strong></td><td class="weighted"><strong>{s["weighted_total"]:.2f}</strong></td></tr>',
                    '    </table>',
                    '  </div>',
                    '',
                    '  <div class="section">',
                    '    <h2>💰 Asset Analysis</h2>',
                    '    <table>',
                    '      <tr><th>Symbol</th><th>Name</th><th>Price</th><th>24h Change</th></tr>',
                ]

                # Add all assets with their technical indicators if available
                for sym, a in assets.items():
                    price = f"${a.get('price', 0):,.2f}" if a.get('price') else "N/A"
                    change = a.get('change_24h', 0)
                    change_str = f'<span class="{"positive" if change > 0 else "negative" if change < 0 else "neutral"}">{change:+.2f}%</span>' if change is not None else "N/A"
                    html_lines.append(f'      <tr><td>{sym}</td><td>{a["name"]}</td><td>{price}</td><td>{change_str}</td></tr>')

                html_lines.extend([
                    '    </table>',
                    '  </div>',
                    '',
                    '  <div class="section">',
                    '    <h2>🔧 BTC Technical Indicators</h2>',
                    '    <table>',
                    '      <tr><th>Indicator</th><th>Value</th><th>Analysis</th></tr>',
                    f'      <tr><td>RSI (14-day)</td><td>{rsi_display}</td><td>{rsi_status}</td></tr>',
                    f'      <tr><td>SMA30</td><td>{sma30_display}</td><td>Price is {"below" if btc_price_val < sma30_val else "above"} 30-day average</td></tr>',
                    f'      <tr><td>WMA200</td><td>{wma200_display}</td><td>Long-term trend reference</td></tr>',
                    f'      <tr><td>Trend</td><td>{trend_display}</td><td>{trend_status}</td></tr>',
                    f'      <tr><td>24h Change</td><td>{btc_change_val:+.2f}%</td><td>{"Down" if btc_change_val < 0 else "Up"}</td></tr>',
                    f'      <tr><td>PPO Histogram</td><td>{ppo_display}</td><td>{"Bullish momentum" if ppo_hist and ppo_hist > 0 else "Bearish momentum" if ppo_hist else "Neutral"}</td></tr>',
                    '    </table>',
                    '    <p><strong>Analysis:</strong> ',
                    f'      {tech_rationale}',
                    '    </p>',
                    '  </div>',
                    '',
                    '  <div class="section">',
                    '    <h2>⚙️ Fundamentals Overview</h2>',
                    '    <ul style="list-style: none; padding: 0;">',
                ])

                # Hash rate
                btc_hash = report_data.get('onchain', {}).get('btc_hash_rate')
                hash_change = report_data.get('onchain', {}).get('btc_hash_rate_change_24h')
                if btc_hash:
                    change_str = f" (24h change: {hash_change:+.2f}%)" if hash_change is not None else ""
                    html_lines.append(f'      <li><strong>BTC Hash Rate:</strong> {btc_hash:,.0f} TH/s{change_str}</li>')
                else:
                    html_lines.append('      <li>BTC Hash Rate: Data unavailable</li>')

                # Halving info
                halving_last = report_data.get('onchain', {}).get('halving_last')
                halving_next = report_data.get('onchain', {}).get('halving_next_estimate')
                halving_days_since = report_data.get('onchain', {}).get('halving_days_since')
                halving_days_until = report_data.get('onchain', {}).get('halving_days_until')
                if halving_last and halving_days_since:
                    html_lines.append(f'      <li><strong>Last BTC Halving:</strong> {halving_last} ({halving_days_since} days ago)</li>')
                if halving_next and halving_days_until:
                    html_lines.append(f'      <li><strong>Next BTC Halving:</strong> {halving_next} — in {halving_days_until} days</li>')

                # Halving phase
                if halving_days_since is not None:
                    ds = halving_days_since
                    phase = "Early Post-Halving (Bullish Phase)" if ds < 300 else "Mid Post-Halving (Peak Bullish)" if ds < 550 else "Late Post-Halving (Distribution/Bear Risk)"
                    html_lines.append(f'      <li><strong>Halving Cycle Phase:</strong> {phase}</li>')

                # Miner revenue and difficulty
                miner_rev = report_data.get('onchain', {}).get('miner_revenue_usd')
                fees = report_data.get('onchain', {}).get('total_fees_usd')
                diff = report_data.get('onchain', {}).get('difficulty')
                diff_change = report_data.get('onchain', {}).get('difficulty_change_pct')
                if miner_rev is not None:
                    rev_str = f"${miner_rev:,.0f}"
                    if fees is not None and fees > 0:
                        fee_pct = (fees / miner_rev) * 100
                        html_lines.append(f'      <li><strong>Miner Revenue (24h):</strong> {rev_str} (fees: ${fees:,.0f}, {fee_pct:.1f}% of revenue)</li>')
                    else:
                        html_lines.append(f'      <li><strong>Miner Revenue (24h):</strong> {rev_str}</li>')
                if diff is not None:
                    diff_str = f"{diff:,.0f}"
                    if diff_change is not None:
                        diff_str += f" (2w change: {diff_change:+.2f}%)"
                    html_lines.append(f'      <li><strong>Network Difficulty:</strong> {diff_str}</li>')

                html_lines.append('    </ul>')
                html_lines.append('  </div>')
                html_lines.append('')
                html_lines.append('  <div class="section">')
                html_lines.append('    <h2>📰 Sentiment Analysis</h2>')
                html_lines.append(f'    <p><strong>Fear & Greed Index:</strong> <span class="{"negative" if fng_val < 25 else "neutral" if fng_val < 50 else "positive"}">{fng_val}</span> ({fng_lbl})</p>')
                html_lines.append(f'    <p><strong>News Sentiment Score:</strong> {news_sent:.3f} (-1 to +1)</p>')
                if pos_kw:
                    html_lines.append(f'    <p><strong>Positive keywords:</strong> {", ".join(pos_kw)}</p>')
                if neg_kw:
                    html_lines.append(f'    <p><strong>Negative keywords:</strong> {", ".join(neg_kw)}</p>')

                # Top headlines
                if news_items:
                    html_lines.append('    <h3>Top Headlines</h3>')
                    for item in news_items[:5]:
                        title = item.get('title', 'No title')
                        link = item.get('link', '#')
                        source = item.get('source', 'Unknown')
                        html_lines.append(f'    <div class="news-item"><span class="news-title"><a href="{link}">{title}</a></span><span class="news-source">— {source}</span></div>')

                html_lines.append('  </div>')
                html_lines.append('')
                html_lines.append('  <div class="section">')
                html_lines.append('    <h2>⚠️ Risk Assessment</h2>')
                html_lines.append(f'    <p><strong>Overall Risk Score:</strong> {risk_score:.3f} / 1.0</p>')
                html_lines.append(f'    <p><strong>Adjusted Score:</strong> {risks_adj_score:.1f} / 10.0</p>')
                if risk_factors:
                    html_lines.append('    <p><strong>Risk Factors Detected:</strong></p><ul>')
                    for factor in risk_factors:
                        html_lines.append(f'      <li>{factor}</li>')
                    html_lines.append('    </ul>')
                else:
                    html_lines.append('    <p><strong>No significant risk factors detected.</strong></p>')
                html_lines.append('    <p><strong>Context:</strong><br>')
                html_lines.append(f'      News sentiment: {news_sent:.3f} | BTC dominance: {btc_dom:.1f}%')
                if wma200_dist is not None:
                    html_lines.append(f' | BTC vs WMA200: {wma200_dist:+.1f}%')
                html_lines.append('    </p>')
                html_lines.append('  </div>')
                html_lines.append('')
                html_lines.append('  <div class="section">')
                html_lines.append('    <h2>💡 Verdict Rationale</h2>')
                html_lines.append(f'    <p>The <strong>{verdict}</strong> recommendation is based on a weighted composite score of <strong>{report_data["confidence"]}/10</strong>.</p>')
                html_lines.append('    <ul>')
                html_lines.append(f'      <li><strong>Technical:</strong> {tech_rationale}</li>')
                html_lines.append(f'      <li><strong>Sentiment:</strong> Fear & Greed at {fng_val} ({fng_lbl})</li>')
                html_lines.append(f'      <li><strong>News tone:</strong> {"Positive" if news_sent > 0.1 else "Negative" if news_sent < -0.1 else "Neutral"}</li>')
                html_lines.append(f'      <li><strong>Risk factors:</strong> {len(risk_factors)} identified: {"; ".join(risk_factors) if risk_factors else "Minimal"}</li>')
                html_lines.append('    </ul>')
                html_lines.append('  </div>')
                html_lines.append('')
                html_lines.append('  <div class="section">')
                html_lines.append('    <h2>📋 Methodology</h2>')
                html_lines.append('    <ul>')
                html_lines.append('      <li><strong>Data sources:</strong> CoinGecko API, Alternative.me, Blockchain.info, RSS news feeds</li>')
                html_lines.append('      <li><strong>Technical indicators:</strong> RSI (14-day), SMA30, PPO (12/26/9), Volume MA(30)</li>')
                html_lines.append('      <li><strong>Technical score:</strong> Weighted combination of RSI, trend, PPO histogram, volume, Fear & Greed</li>')
                html_lines.append('      <li><strong>Sentiment:</strong> Keyword-based analysis of recent news headlines</li>')
                html_lines.append('      <li><strong>Risk assessment:</strong> Aggregates negative news keywords, regulatory mentions, BTC dominance</li>')
                html_lines.append('    </ul>')
                html_lines.append('  </div>')
                html_lines.append('')
                html_lines.append('  <div class="disclaimer">')
                html_lines.append('    <p>⚠️ <em>This is for informational purposes only. Not financial advice.</em></p>')
                html_lines.append('    <p>📈 Generated by Crypto Reporter v1.0 | Part of OpenClaw</p>')
                html_lines.append('  </div>')
                html_lines.append('</body>')
                html_lines.append('</html>')

                html_body = '\n'.join(html_lines)

                # Send email via gog
                logger.info(f"Sending email to {email_recipient} via gog...")
                result = subprocess.run(
                    ['/home/linuxbrew/.linuxbrew/bin/gog', 'gmail', 'send', '--to', email_recipient, '--subject', subject, '--body-html', html_body],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logger.info(f"✓ Email sent successfully to {email_recipient}")
                else:
                    logger.error(f"✗ Email send failed (exit {result.returncode}): {result.stderr or result.stdout}")

            except Exception as e:
                logger.error(f"Email notification failed: {e}", exc_info=True)
                html_body = '\n'.join(html_lines)

                # Send email via gog with HTML content directly
                logger.info(f"Sending email to {email_recipient} via gog...")
                result = subprocess.run(
                    ['/home/linuxbrew/.linuxbrew/bin/gog', 'gmail', 'send', '--to', email_recipient, '--subject', subject, '--body-html', html_body],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logger.info(f"✓ Email sent successfully to {email_recipient}")
                else:
                    logger.error(f"✗ Email send failed (exit {result.returncode}): {result.stderr or result.stdout}")

            except Exception as e:
                logger.error(f"Email notification failed: {e}", exc_info=True)

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
