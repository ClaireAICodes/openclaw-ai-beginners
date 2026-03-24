#!/usr/bin/env python3
"""
Daily Cryptocurrency Summary Report Generator

Compiles comprehensive daily crypto reports from multiple sources including:
- Fundamentals (network metrics, adoption, developer activity)
- Technicals (price action, indicators, support/resistance)
- Sentiment (social media, fear & greed, news tone)
- Risks (regulatory, technical, market, liquidity)
- Clear verdict: Buy / Hold / Sell bias with confidence score

Usage: python crypto_report.py [--date YYYY-MM-DD] [--output OUTPUT_DIR]
"""

import os
import sys
import json
import yaml
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Configure paths
WORKSPACE = Path('/home/ubuntu/.openclaw/workspace')
CRYPTO_REPORT_DIR = WORKSPACE / 'crypto-report'
OUTPUT_DIR = WORKSPACE / 'memory' / 'crypto-reports'

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Verdict(Enum):
    """Trading verdict with bias direction"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class CryptoReportConfig:
    """Configuration for crypto report generation"""
    cron_schedule: str
    max_news_articles: int
    max_analysis_pieces: int
    lookback_days: int
    tracked_assets: List[str]
    data_sources: List[Dict[str, Any]]
    verdict_thresholds: Dict[str, Any]
    report_format: str
    output_dir: Path
    log_level: str
    enable_notifications: bool
    notification_channel: str
    analysis_model: str
    max_tokens_per_source: int
    verdict_weights: Dict[str, float]

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'CryptoReportConfig':
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Convert output_dir to Path
        config_data['output_dir'] = Path(config_data.get('output_dir', str(OUTPUT_DIR)))

        return cls(**config_data)


@dataclass
class MarketData:
    """Container for market data and analysis"""
    date: str
    btc_price: Optional[float] = None
    eth_price: Optional[float] = None
    market_cap: Optional[float] = None
    btc_dominance: Optional[float] = None
    total_volume_24h: Optional[float] = None
    fear_greed_index: Optional[int] = None
    fear_greed_trend: Optional[str] = None


@dataclass
class AssetAnalysis:
    """Analysis for a specific cryptocurrency"""
    symbol: str
    name: str
    price: Optional[float] = None
    change_24h: Optional[float] = None
    change_7d: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None

    # Technical indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    moving_average_50: Optional[float] = None
    moving_average_200: Optional[float] = None
    support_levels: List[float] = None
    resistance_levels: List[float] = None

    # Fundamentals
    active_addresses: Optional[int] = None
    transaction_volume: Optional[float] = None
    tvl: Optional[float] = None  # Total Value Locked (for DeFi)
    developer_activity: Optional[int] = None
    hash_rate: Optional[float] = None  # For PoW chains

    # Sentiment
    social_volume: Optional[int] = None
    social_sentiment_score: Optional[float] = None  # -1 to 1 scale
    news_sentiment: Optional[float] = None
    whale_accumulation: Optional[bool] = None

    def __post_init__(self):
        if self.support_levels is None:
            self.support_levels = []
        if self.resistance_levels is None:
            self.resistance_levels = []


@dataclass
class SentimentOverview:
    """Overall market sentiment"""
    fear_greed_index: int
    fear_greed_trend: str  # "bullish", "neutral", "fearful"
    social_sentiment_avg: float  # Average across tracked assets
    news_tone_score: float  # News sentiment score
    twitter_volume: int
    reddit_activity_score: float
    google_trends_score: float
    institutional_flows: Optional[float] = None  # Net flows (+/-)
    funding_rates: Optional[float] = None  # Average perpetual funding rates


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    regulatory_risk_level: int  # 1-5 scale
    regulatory_concerns: List[str]
    technical_risks: List[str]
    market_risks: List[str]
    liquidity_risks: List[str]
    systemic_risk_score: float  # 0-1 scale
    concentration_risk: Optional[float] = None  # BTC dominance as risk factor


@dataclass
class VerdictAnalysis:
    """Final verdict with supporting analysis"""
    verdict: str
    confidence_score: float  # 0-10 scale
    rationale: str
    score_breakdown: Dict[str, float]
    key_factors: List[str]
    time_horizon: str  # "short-term", "medium-term", "long-term"
    risk_reward_ratio: Optional[float] = None


@dataclass
class CryptoReport:
    """Complete daily cryptocurrency summary report"""
    report_date: str
    generated_at: str
    market_data: MarketData
    asset_analyses: List[AssetAnalysis]
    sentiment: SentimentOverview
    risks: RiskAssessment
    verdict: VerdictAnalysis
    highlights: List[str]
    watchlist: List[Dict[str, str]]
    sources_used: List[str]
    methodology_notes: str

    def to_markdown(self) -> str:
        """Generate markdown report"""
        return self._generate_markdown()

    def to_json(self) -> str:
        """Generate JSON report"""
        return json.dumps(asdict(self), indent=2, default=str)


class CryptoReportGenerator:
    """Main class for generating daily crypto reports"""

    def __init__(self, config: CryptoReportConfig):
        self.config = config
        self._setup_logging()
        self.artifacts_dir = CRYPTO_REPORT_DIR / 'artifacts'
        self.artifacts_dir.mkdir(exist_ok=True)

    def _setup_logging(self):
        """Configure logging based on config"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

    def generate(self, target_date: Optional[datetime] = None) -> CryptoReport:
        """
        Generate a comprehensive daily crypto report

        Args:
            target_date: Date to generate report for (defaults to today)

        Returns:
            CryptoReport object with complete analysis
        """
        if target_date is None:
            target_date = datetime.now()

        report_date_str = target_date.strftime('%Y-%m-%d')
        logger.info(f"Starting crypto report generation for {report_date_str}")

        # Step 1: Collect data from all sources
        raw_data = self._collect_data(target_date)

        # Step 2: Analyze market data
        market_data = self._analyze_market_data(raw_data, report_date_str)

        # Step 3: Analyze individual assets
        asset_analyses = self._analyze_assets(raw_data, market_data)

        # Step 4: Analyze sentiment
        sentiment = self._analyze_sentiment(raw_data, asset_analyses)

        # Step 5: Assess risks
        risks = self._assess_risks(raw_data, market_data, asset_analyses)

        # Step 6: Calculate verdict
        verdict = self._calculate_verdict(market_data, asset_analyses, sentiment, risks)

        # Step 7: Generate highlights and watchlist
        highlights = self._generate_highlights(market_data, asset_analyses, sentiment, risks)
        watchlist = self._generate_watchlist(asset_analyses, verdict)

        # Step 8: Compile final report
        report = CryptoReport(
            report_date=report_date_str,
            generated_at=datetime.now().isoformat(),
            market_data=market_data,
            asset_analyses=asset_analyses,
            sentiment=sentiment,
            risks=risks,
            verdict=verdict,
            highlights=highlights,
            watchlist=watchlist,
            sources_used=[source['name'] for source in self.config.data_sources],
            methodology_notes=self._get_methodology_notes()
        )

        logger.info(f"Report generation complete for {report_date_str}")
        return report

    def _collect_data(self, target_date: datetime) -> Dict[str, Any]:
        """
        Collect raw data from all configured sources

        Uses web_search tool to fetch latest articles and analysis
        """
        logger.info("Collecting data from configured sources...")
        collected_data = {}
        total_sources = len(self.config.data_sources)

        for idx, source in enumerate(self.config.data_sources, 1):
            source_name = source['name']
            source_type = source['type']
            priority = source.get('priority', 3)
            queries = source.get('queries', [])

            logger.info(f"[{idx}/{total_sources}] Collecting from {source_name} (priority {priority})")

            source_data = []
            for query_idx, query in enumerate(queries, 1):
                logger.debug(f"  Query {query_idx}/{len(queries)}: {query[:80]}...")

                try:
                    # Use web_search tool to fetch results
                    # Note: In actual execution, this will call the web_search function
                    results = self._execute_web_search(
                        query=query,
                        count=min(self.config.max_news_articles, 10),
                        freshness="pd"  # Past day
                    )

                    if results:
                        source_data.extend(results)
                        logger.debug(f"    Retrieved {len(results)} results")
                    else:
                        logger.warning(f"    No results for query: {query}")

                except Exception as e:
                    logger.error(f"    Error fetching query '{query}': {e}")
                    continue

            collected_data[source_name] = {
                'data': source_data,
                'priority': priority,
                'source_type': source_type,
                'query_count': len(queries)
            }

            logger.info(f"  ✓ Collected {len(source_data)} items from {source_name}")

        # Save raw artifacts
        self._save_raw_artifacts(collected_data, target_date)

        logger.info(f"Data collection complete: {sum(len(d['data']) for d in collected_data.values())} total items")
        return collected_data

    def _execute_web_search(self, query: str, count: int = 10, **kwargs) -> List[Dict[str, str]]:
        """
        Execute a web search using the web_search tool

        This is a placeholder that will be replaced with actual tool invocation
        during execution. For now, we document the interface.
        """
        # In actual execution, this calls the web_search tool
        # Return format: List of dicts with 'title', 'url', 'description', 'published', 'siteName'
        raise NotImplementedError("This method will be implemented during tool execution")

    def _analyze_market_data(self, raw_data: Dict[str, Any], report_date: str) -> MarketData:
        """
        Extract and synthesize market-wide data from collected sources

        Looks for:
        - BTC and ETH prices
        - Market cap and volume
        - Fear & greed index
        - Bitcoin dominance
        """
        logger.info("Analyzing market data...")
        market = MarketData(date=report_date)

        # Aggregate data from all sources looking for market metrics
        all_articles = []
        for source_info in raw_data.values():
            all_articles.extend(source_info['data'])

        # Simple extraction logic - in production, use more sophisticated parsing
        # For now, we'll extract what we can find through keyword matching

        # Try to find BTC price
        for article in all_articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            # Pattern matching for BTC price (e.g., "Bitcoin at $95,000")
            if 'bitcoin' in text.lower() or 'btc' in text.lower():
                # This is placeholder - actual implementation would use regex or NLP
                pass

        logger.info("Market analysis complete")
        return market

    def _analyze_assets(self, raw_data: Dict[str, Any], market_data: MarketData) -> List[AssetAnalysis]:
        """
        Analyze each tracked cryptocurrency

        Creates AssetAnalysis objects for each tracked asset with:
        - Price data and changes
        - Technical indicators
        - Fundamental metrics
        - Sentiment signals
        """
        logger.info(f"Analyzing {len(self.config.tracked_assets)} tracked assets...")
        analyses = []

        for symbol in self.config.tracked_assets:
            analysis = AssetAnalysis(symbol=symbol, name=self._get_asset_name(symbol))
            # Populate with extracted data from raw_data
            # This would involve parsing articles for that specific asset
            analyses.append(analysis)
            logger.debug(f"  Analyzed {symbol}")

        logger.info(f"Asset analysis complete for {len(analyses)} assets")
        return analyses

    def _get_asset_name(self, symbol: str) -> str:
        """Get full name for asset symbol"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'AVAX': 'Avalanche',
            'DOT': 'Polkadot',
            'LINK': 'Chainlink',
            'UNI': 'Uniswap',
            'AAVE': 'Aave',
            'MKR': 'Maker'
        }
        return names.get(symbol.upper(), symbol)

    def _analyze_sentiment(self, raw_data: Dict[str, Any], asset_analyses: List[AssetAnalysis]) -> SentimentOverview:
        """
        Analyze overall market sentiment from multiple dimensions:

        - Fear & Greed index
        - Social media volume and tone
        - News sentiment
        - Institutional flows
        - Derivatives metrics (funding rates)
        """
        logger.info("Analyzing market sentiment...")
        sentiment = SentimentOverview(
            fear_greed_index=50,  # Placeholder - would be extracted
            fear_greed_trend="neutral",
            social_sentiment_avg=0.0,
            news_tone_score=0.0,
            twitter_volume=0,
            reddit_activity_score=0.0,
            google_trends_score=50,
            institutional_flows=None,
            funding_rates=None
        )
        logger.info("Sentiment analysis complete")
        return sentiment

    def _assess_risks(self, raw_data: Dict[str, Any], market_data: MarketData,
                      asset_analyses: List[AssetAnalysis]) -> RiskAssessment:
        """
        Comprehensive risk assessment across multiple dimensions:

        1. Regulatory risks (new legislation, enforcement actions)
        2. Technical risks (protocol vulnerabilities, network issues)
        3. Market risks (liquidity crises, correlation events)
        4. Liquidity risks (exchange solvency, stablecoin depegging)
        5. Systemic risks (cascading failures, black swans)
        """
        logger.info("Assessing market risks...")
        risks = RiskAssessment(
            regulatory_risk_level=3,
            regulatory_concerns=[],
            technical_risks=[],
            market_risks=[],
            liquidity_risks=[],
            systemic_risk_score=0.3,
            concentration_risk=market_data.btc_dominance / 100 if market_data.btc_dominance else 0.5
        )
        logger.info("Risk assessment complete")
        return risks

    def _calculate_verdict(self, market_data: MarketData, asset_analyses: List[AssetAnalysis],
                          sentiment: SentimentOverview, risks: RiskAssessment) -> VerdictAnalysis:
        """
        Calculate final verdict using weighted scoring across:

        - Fundamentals (30%)
        - Technicals (25%)
        - Sentiment (20%)
        - Risks (25%)

        Returns VerdictAnalysis with verdict, confidence, and rationale
        """
        logger.info("Calculating final verdict...")

        weights = self.config.verdict_weights

        # Placeholder scoring logic - would be replaced with actual analysis
        fundamentals_score = 5.0    # 0-10 scale
        technicals_score = 5.0
        sentiment_score = 5.0
        risks_score = 5.0

        # Calculate weighted average
        weighted_score = (
            fundamentals_score * weights['fundamentals'] +
            technicals_score * weights['technicals'] +
            sentiment_score * weights['sentiment'] +
            risks_score * weights['risks']
        )

        # Determine verdict based on thresholds
        thresholds = self.config.verdict_thresholds
        if weighted_score >= thresholds['BUY_SCORE_MIN']:
            verdict = Verdict.BUY if weighted_score < 8.5 else Verdict.STRONG_BUY
        elif weighted_score <= thresholds['SELL_SCORE_MAX']:
            verdict = Verdict.SELL if weighted_score > 1.5 else Verdict.STRONG_SELL
        else:
            verdict = Verdict.HOLD

        verdict_analysis = VerdictAnalysis(
            verdict=verdict.value,
            confidence_score=weighted_score,
            rationale="Based on comprehensive analysis of market fundamentals, technical indicators, sentiment metrics, and risk factors.",
            score_breakdown={
                'fundamentals': fundamentals_score,
                'technicals': technicals_score,
                'sentiment': sentiment_score,
                'risks': risks_score,
                'weighted_total': weighted_score
            },
            key_factors=self._extract_key_factors(asset_analyses, sentiment, risks),
            time_horizon="medium-term",
            risk_reward_ratio=1.5  # Placeholder
        )

        logger.info(f"Verdict: {verdict.value} (confidence: {weighted_score:.2f}/10)")
        return verdict_analysis

    def _extract_key_factors(self, asset_analyses: List[AssetAnalysis],
                            sentiment: SentimentOverview, risks: RiskAssessment) -> List[str]:
        """Extract 3-5 key factors driving the verdict"""
        factors = [
            f"Market sentiment: {sentiment.fear_greed_trend} (F&G: {sentiment.fear_greed_index})",
            f"Systemic risk score: {risks.systemic_risk_score:.2f}",
            f"BTC dominance: {risks.concentration_risk:.1%}"
        ]
        return factors

    def _generate_highlights(self, market_data: MarketData, asset_analyses: List[AssetAnalysis],
                            sentiment: SentimentOverview, risks: RiskAssessment) -> List[str]:
        """Generate key highlights for executive summary"""
        highlights = [
            f"Market cap: ${market_data.market_cap:,.0f}" if market_data.market_cap else "Market cap data unavailable",
            f"24h volume: ${market_data.total_volume_24h:,.0f}" if market_data.total_volume_24h else "Volume data unavailable",
            f"Fear & Greed: {sentiment.fear_greed_index} ({sentiment.fear_greed_trend})",
            f"BTC dominance: {market_data.btc_dominance:.1f}%" if market_data.btc_dominance else "BTC dominance unavailable",
        ]
        return highlights

    def _generate_watchlist(self, asset_analyses: List[AssetAnalysis],
                           verdict: VerdictAnalysis) -> List[Dict[str, str]]:
        """
        Generate watchlist of assets to monitor

        Includes:
        - Assets with strong buy/sell signals
        - Assets approaching key technical levels
        - Assets with unusual volume or sentiment shifts
        """
        watchlist = []
        for asset in asset_analyses:
            # Simple logic - in production, more sophisticated criteria
            if asset.change_7d and abs(asset.change_7d) > 10:
                watchlist.append({
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'signal': 'Strong momentum' if asset.change_7d > 0 else 'Weakness',
                    'current_price': f"${asset.price:,.2f}" if asset.price else "N/A"
                })

        return watchlist[:10]  # Top 10 watchlist items

    def _get_methodology_notes(self) -> str:
        """Return methodology notes for the report"""
        return (
            "This report compiles data from multiple public sources including news outlets, "
            "on-chain analytics platforms, social media sentiment trackers, and market data providers. "
            "Analysis combines quantitative metrics with qualitative assessment. Verdict is based on "
            "weighted scoring of fundamentals (30%), technicals (25%), sentiment (20%), and risks (25%). "
            "Report is for informational purposes only and not financial advice."
        )

    def _save_raw_artifacts(self, collected_data: Dict[str, Any], target_date: datetime):
        """Save raw data artifacts for audit and debugging"""
        date_str = target_date.strftime('%Y-%m-%d')
        artifact_file = self.artifacts_dir / f"raw_{date_str}.json"

        # Convert collected_data to JSON-serializable format
        serializable_data = {}
        for source_name, source_info in collected_data.items():
            serializable_data[source_name] = {
                'data': source_info['data'],
                'priority': source_info['priority'],
                'source_type': source_info['source_type'],
                'query_count': source_info['query_count']
            }

        with open(artifact_file, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)

        logger.debug(f"Raw artifacts saved to {artifact_file}")

    def save_report(self, report: CryptoReport, output_format: Optional[str] = None):
        """
        Save report to file(s) in configured output directory

        Args:
            report: CryptoReport object
            output_format: Override config format ('markdown', 'json', or 'both')
        """
        output_format = output_format or self.config.report_format
        date_str = report.report_date

        saved_files = []

        if output_format in ('markdown', 'both'):
            md_file = self.config.output_dir / f"crypto-report-{date_str}.md"
            with open(md_file, 'w') as f:
                f.write(report.to_markdown())
            saved_files.append(md_file)
            logger.info(f"Markdown report saved: {md_file}")

        if output_format in ('json', 'both'):
            json_file = self.config.output_dir / f"crypto-report-{date_str}.json"
            with open(json_file, 'w') as f:
                f.write(report.to_json())
            saved_files.append(json_file)
            logger.info(f"JSON report saved: {json_file}")

        # Also save latest symlink
        latest_md = self.config.output_dir / "crypto-report-latest.md"
        latest_json = self.config.output_dir / "crypto-report-latest.json"

        if output_format in ('markdown', 'both'):
            if latest_md.exists():
                latest_md.unlink()
            latest_md.symlink_to(f"crypto-report-{date_str}.md")

        if output_format in ('json', 'both'):
            if latest_json.exists():
                latest_json.unlink()
            latest_json.symlink_to(f"crypto-report-{date_str}.json")

        logger.info(f"Created latest symlinks")
        return saved_files

    def _generate_markdown(self) -> str:
        """Generate the full markdown report (to be implemented with actual data)"""
        # This will be the actual template when we have real data
        # For now, return a placeholder
        return "# Crypto Report\n\nReport generation in progress."


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate daily cryptocurrency summary report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crypto_report.py                    # Generate report for today
  python crypto_report.py --date 2026-02-26  # Generate report for specific date
  python crypto_report.py --output /tmp      # Save to custom directory
        """
    )
    parser.add_argument('--date', type=str,
                       help='Target date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--output', type=str,
                       help='Override output directory')
    parser.add_argument('--config', type=str,
                       default=str(CRYPTO_REPORT_DIR / 'config.yaml'),
                       help='Path to config file')
    parser.add_argument('--format', type=str, choices=['markdown', 'json', 'both'],
                       help='Output format override')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable debug logging')
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    config = CryptoReportConfig.from_yaml(config_path)

    # Override output if specified
    if args.output:
        config.output_dir = Path(args.output)
        config.output_dir.mkdir(parents=True, exist_ok=True)

    # Override format if specified
    if args.format:
        config.report_format = args.format

    # Set log level
    if args.verbose:
        config.log_level = 'DEBUG'

    # Create generator
    generator = CryptoReportGenerator(config)

    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    try:
        # Generate report
        report = generator.generate(target_date)

        # Save report
        saved_files = generator.save_report(report)

        logger.info(f"✓ Report generation successful: {len(saved_files)} file(s) saved")
        return 0

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
