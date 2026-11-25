import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from textblob import TextBlob
import requests

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "SBIN.NS", "INFY.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS",
    "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "NTPC.NS", "AXISBANK.NS",
    "M&M.NS", "WIPRO.NS", "COALINDIA.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "HAL.NS", "BEL.NS", "DLF.NS", "TRENT.NS", "ETERNAL.NS"
]

def add_indicators(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    tr = np.max(pd.concat([
        df['High'] - df['Low'],
        np.abs(df['High'] - df['Close'].shift()),
        np.abs(df['Low'] - df['Close'].shift())
    ], axis=1), axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    return df

def get_news_sentiment(sym):
    try:
        feed = feedparser.parse(f"https://google.com{sym.replace('.NS','')}+share+news+india&hl=en-IN&gl=IN&ceid=IN:en")
        scores = [TextBlob(e.title).sentiment.polarity for e in feed.entries[:5]]
        avg = np.mean(scores) if scores else 0
        if avg > 0.05:
            return "🟢 POSITIVE"
        if avg < -0.05:
            return "🔴 NEGATIVE"
    except Exception:
        pass
    return "🟡 NEUTRAL"

def send_telegram_alert(token, chat_id, msg):
    if token and chat_id:
        try:
            requests.post(
                f"https://telegram.org{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                timeout=5
            )
        except Exception:
            pass

def run_quant_scan(capital=100000, risk_pct=0.02, tg_token="", tg_chat_id=""):
    nifty = yf.download("^NSEI", period="3mo", interval="1d", progress=False)
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)
    nifty['EMA_50'] = nifty['Close'].ewm(span=50, adjust=False).mean()
    curr_n = round(float(nifty['Close'].iloc[-1]), 2)
    bullish = curr_n > float(nifty['EMA_50'].iloc[-1])
    n_1m = ((curr_n / float(nifty['Close'].iloc[-21])) - 1) * 100

    raw = yf.download(WATCHLIST, period="1y", interval="1d", group_by="ticker", progress=False)
    rows, dfs = [], {}

    for t in WATCHLIST:
        try:
            if t not in raw.columns.get_level_values(0):
                continue
            df = raw[t].dropna().copy()
            if len(df) < 55:
                continue
            df = add_indicators(df)
            sym = t.replace(".NS", "")
            dfs[sym] = df
            last = df.iloc[-1]

            p = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 2)
            e20, e50 = float(last['EMA_20']), float(last['EMA_50'])
            macd, sig = float(last['MACD']), float(last['Signal'])
            atr = float(last['ATR'])
            vr = round(float(last['Vol_Ratio']), 2)
            alpha = round((((p / float(df['Close'].iloc[-21])) - 1) * 100) - n_1m, 2)
            res20 = round(float(df['High'].tail(20).max()), 2)
            sup20 = round(float(df['Low'].tail(20).min()), 2)

            sc = (30 if p > e20 > e50 else (15 if p > e20 else 0)) + \
                 (25 if rsi < 35 else (20 if 45 <= rsi <= 65 else 0)) + \
                 (20 if macd > sig else 0) + (15 if vr > 1.15 else 0) + (15 if alpha > 2.0 else 0)

            if sc >= 85:
                grade, mult = "A+ STRONG BUY", 1.0
            elif sc >= 70:
                grade, mult = "A BUY SETUP", 0.75
            elif sc >= 55:
                grade, mult = "WATCHLIST", 0.0
            else:
                grade, mult = "NEUTRAL", 0.0

            news = get_news_sentiment(t) if sc >= 70 else "SKIPPED"
            if "NEGATIVE" in news and sc >= 70:
                grade, mult = "VETOED (NEWS)", 0.0

            sl = round(max(p - (1.5 * atr), sup20 * 0.99), 2)
            tgt = round(p + (3.0 * atr), 2)
            qty = max(1, int(((capital * risk_pct) * mult) / max(p - sl, 1))) if mult > 0 else int((capital * 0.05) / max(p, 1))

            rows.append({
                "Symbol": sym, "LTP (₹)": p, "Score": sc, "Signal": grade,
                "Alpha (1M)": alpha, "RSI": rsi, "Support (₹)": sup20,
                "Resistance (₹)": res20, "Stop Loss (₹)": sl, "Target (₹)": tgt,
                "Qty": qty, "News": news
            })

            if sc >= 80 and "VETOED" not in grade:
                send_telegram_alert(tg_token, tg_chat_id, f"🚨 *QUANTDESK ALERT: {sym}*\n• {grade} ({sc}/100)\n• Entry: ₹{p} | SL: ₹{sl} | Target: ₹{tgt} | Qty: {qty}")
        except Exception:
            continue

    df_res = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True) if rows else pd.DataFrame()
    return df_res, dfs, curr_n, n_1m, bullish
