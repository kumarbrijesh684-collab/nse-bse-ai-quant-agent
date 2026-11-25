# 🏛️ NSE/BSE Institutional AI Quantitative Trading & Sentiment Agent (v4.0)

![Python](https://shields.io)
![Market](https://shields.io)
![Architecture](https://shields.io)
![Cost](https://shields.io)

An end-to-end, regime-aware **Quantitative Trading Signal, NLP News Sentiment, Risk Management, and Historical Backtesting Engine** engineered specifically for the **Indian Stock Market (NSE/BSE)**. 

Built on a zero-cost, cloud-native Python pipeline, this system eliminates emotional trading by combining multi-timeframe technical indicators, relative strength alpha filtering, and automated headline sentiment vetoing with volatility-adjusted position sizing.

---

## 🚀 Key System Capabilities

* **🌐 Macro Market Regime Filter:** Evaluates the benchmark **Nifty 50 (`^NSEI`)** trend against its 50-day Exponential Moving Average (EMA) to dynamically classify market conditions (`BULLISH` vs. `BEARISH/CAUTIOUS`) before approving long setups.
* **📊 Multi-Factor Swing Scanner (Full Nifty 50 Universe):** Scores all 50 Nifty equities (0–100) using a weighted confluence of **20/50 EMA Trend Alignment**, **RSI (14) Momentum**, **MACD Crossovers**, **Relative Volume Spikes**, and **1-Month Alpha vs. Nifty 50**.
* **⚡ Intraday Momentum & VWAP Scanner (15-Min Timeframe):** Tracks intraday price action relative to **Volume Weighted Average Price (VWAP)** and short-term EMAs for high-probability intraday setups.
* **📰 Automated NLP News Sentiment Gatekeeper:** Scrapes live Indian financial news via Google News RSS feeds and computes polarity scores using Natural Language Processing (`TextBlob`) to automatically block buy signals on stocks facing negative news catalysts.
* **🛡️ ATR & Support-Aware Institutional Risk Engine:** Computes dynamic **Stop-Loss**, **Take-Profit Targets** (strict `1:2` Risk-to-Reward ratio), **20-Day Support/Resistance**, and **Conviction-Based Position Sizing** capped at a strict `2%` max capital risk per trade.
* **🏆 1-Year Historical Backtesting Simulator:** Runs a day-by-day historical simulation over 1 year of NSE market data to validate strategy **Win-Rate (%)**, **Target vs. Stop-Loss hits**, and **Net Return on Investment (ROI)**.
* **📲 Telegram Mobile Alert Integration & Auto-CSV Export:** Exports daily signal reports to CSV for paper-trading logs and supports instant mobile alerts via Telegram Bot API.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                  NSE / BSE DATA & NEWS INGESTION LAYER                  │
│   • Yahoo Finance API (Daily & 15m OHLCV)   • Google News India RSS     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     MACRO & TECHNICAL QUANT ENGINE                      │
│   • Nifty 50 Regime & Alpha   • EMA (20/50), RSI, MACD, ATR, VWAP       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  NLP SENTIMENT & RISK MANAGEMENT LAYER                  │
│   • Negative News Veto Filter   • 2% Max Risk Position Sizer (1:2 R:R)  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  EXECUTION, BACKTESTING & VISUALIZATION                 │
│   • Nifty 50 Signal Matrix   • 1-Yr Backtest Scorecard   • Telegram UI  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

* **Core Engine:** Python 3.10+, `Pandas`, `NumPy`
* **Market Data Pipeline:** `yfinance` (NSE `.NS` & BSE `.BO` tickers)
* **NLP & News Scraping:** `feedparser`, `TextBlob`
* **Visualization & Alerts:** `Plotly` (Interactive Dark-Mode Subplots), `Requests` (Telegram Bot API)
* **Cloud Execution:** Google Colab / GitHub Codespaces

---

## ⚡ Quick Start

1. **Run in Cloud (Zero Setup):** Click the **"Open in Colab"** badge inside the notebook file (`Untitled1.ipynb`) and run all cells sequentially.
2. **Run Locally / Codespaces:**
   ```bash
   git clone https://github.com
   cd nse-bse-ai-quant-agent
   pip install yfinance pandas numpy plotly feedparser textblob requests
   ```

---

## ⚠️ Disclaimer

*This project is engineered strictly for **quantitative research, algorithmic education, and paper-trading simulation**. Market data from free endpoints may experience standard exchange delays. Always validate strategies in a simulated environment and consult a SEBI-registered financial advisor before deploying live capital.*

---

**Architected by Brijesh Kumar Patel** | *Quantitative Trading & AI Automation*
