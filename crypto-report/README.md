# Daily Crypto Summary Report System

A comprehensive, automated cryptocurrency analysis system that runs daily via cron job and generates detailed market reports with Buy/Hold/Sell recommendations.

## 🎯 What It Does

Every day at 6:00 AM UTC, the system automatically:

1. **Fetches Market Data** from multiple free APIs:
   - CoinGecko (prices, market cap, volume, OHLC data)
   - Alternative.me (Fear & Greed Index)
   - Blockchain.info (Bitcoin on-chain metrics)
   - RSS feeds (news sentiment analysis)

2. **Performs Multi-Dimensional Analysis**:
   - **Fundamentals**: Hash rate, market cap dominance, network metrics
   - **Technicals**: RSI, price trends, SMA analysis
   - **Sentiment**: Fear & Greed Index, keyword-based news sentiment
   - **Risks**: Regulatory keywords, market structure risks

3. **Generates Comprehensive Report** with:
   - Executive Summary with clear Buy/Hold/Sell verdict
   - Weighted confidence score (0-10 scale)
   - Detailed breakdown by dimension
   - Asset-by-asset analysis table
   - Risk assessment and rationale

## 📊 Components

### Core Files
- `src/crypto_reporter.py` - Main standalone script (no external dependencies!)
- `config.json` - Asset list, weights, and settings
- `bin/crypto-reporter.sh` - Optional wrapper script
- Reports output to: `/home/ubuntu/.openclaw/workspace/memory/crypto-reports/`

### Tracked Assets
- BTC (Bitcoin) - bitcoin
- ETH (Ethereum) - ethereum  
- ADA (Cardano) - cardano
- SOL (Solana) - solana
- AVAX (Avalanche) - avalanche-2
- DOT (Polkadot) - polkadot
- LINK (Chainlink) - chainlink
- UNI (Uniswap) - uniswap
- AAVE (Aave) - aave
- MKR (Maker) - maker

## 📈 Scoring Methodology

### Weight Distribution
```
Fundamentals: 30% (Network health, on-chain metrics)
Technicals:   25% (RSI, trends, SMA)
Sentiment:    20% (Fear & Greed, news analysis)
Risks:        25% (Regulatory, market risks)
```

### Verdict Thresholds
- **STRONG_BUY**: Score ≥ 8.5
- **BUY**: Score ≥ 7.0
- **HOLD**: Score 4.0-6.9
- **SELL**: Score ≤ 3.0
- **STRONG_SELL**: Score ≤ 1.5

## 🚀 Usage

### Manual Run
```bash
python3 /home/ubuntu/.openclaw/workspace/crypto-report/src/crypto_reporter.py
```

### Cron Job (Already Set Up)
Runs automatically at 6:00 AM UTC daily.

Job ID: `18ec79ca-65ef-4c54-a162-8a4c22a53c73`

View status:
```bash
openclaw cron list
```

### Output Files
- `crypto-report-YYYY-MM-DD.md` - Full markdown report
- `crypto-report-latest.md` - Symlink to most recent report
- `crypto-report-YYYY-MM-DD.json` - Raw data (if configured)

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "TRACKED_ASSETS": ["BTC", "ETH", "ADA"],
  "VERDICT_WEIGHTS": {
    "fundamentals": 0.30,
    "technicals": 0.25,
    "sentiment": 0.20,
    "risks": 0.25
  },
  "VERDICT_THRESHOLDS": {
    "BUY_SCORE_MIN": 7.0,
    "SELL_SCORE_MAX": 3.0
  },
  "REPORT_FORMAT": "markdown"  // "json" or "both"
}
```

## 📱 Telegram Notifications

By default, the system sends a summary to your Telegram (channel: 129156516) when:
- Report is generated successfully
- Errors occur during execution

## 🛠️ Future Enhancements

Potential upgrades:
- [ ] Add more on-chain metrics (TVL, active addresses)
- [ ] Integrate whale tracking APIs
- [ ] Add more sophisticated NLP for sentiment analysis
- [ ] Historical trend comparison
- [ ] Portfolio correlation analysis
- [ ] Custom alerts on unusual patterns
- [ ] Integration with TradingView API

## ⚠️ Disclaimer

**This is for informational purposes only. Not financial advice.**

The system uses publicly available data and makes automated assessments. Always do your own research before making investment decisions.

## 📜 License

Part of OpenClaw - Created for Master Phil 💖
