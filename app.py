import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from textblob import TextBlob
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime

st.set_page_config(page_title="NSE/BSE AI Quant Agent", page_icon="🏛️", layout="wide")

st.title("🏛️ NSE/BSE Institutional AI Quantitative Trading Agent (v4.1)")
st.markdown("**Architected by Brijesh Kumar Patel** | *Regime-Aware Multi-Factor Scanner, NLP News Veto & Risk Engine*")

st.sidebar.header("⚙️ Portfolio & Alert Settings")
capital = st.sidebar.number_input("Virtual Capital (₹)", min_value=10000, value=100000, step=10000)
risk_pct = st.sidebar.slider("Max Risk Per Trade (%)", 0.5, 5.0, 2.0, 0.5) / 100

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Telegram Mobile Alerts")
enable_tg = st.sidebar.checkbox("Enable Telegram Alerts", value=False)
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat_id = st.sidebar.text_input("Chat ID")

def send_telegram(msg):
    if enable_tg and tg_token and tg_chat_id:
        url = f"https://telegram.org{tg_token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except Exception:
            pass

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "SBIN.NS", "INFY.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS",
    "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "NTPC.NS", "AXISBANK.NS",
    "M&M.NS", "WIPRO.NS", "COALINDIA.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "HAL.NS", "BEL.NS", "DLF.NS", "TRENT.NS", "ETERNAL.NS"
]

def compute_indicators(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    df['ATR'] = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1).rolling(14).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    return df

def get_news_sentiment(symbol):
    clean = symbol.replace(".NS", "")
    try:
        feed = feedparser.parse(f"https://google.com{clean}+share+news+india&hl=en-IN&gl=IN&ceid=IN:en")
        scores = [TextBlob(e.title).sentiment.polarity for e in feed.entries[:5]]
        avg = np.mean(scores) if scores else 0
        if avg > 0.05: return "🟢 POSITIVE"
        elif avg < -0.05: return "🔴 NEGATIVE"
    except Exception:
        pass
    return "🟡 NEUTRAL"

if st.button("🚀 Run Live NSE Quant Scan", type="primary"):
    with st.spinner("Batch-Fetching NSE Market Regime & Top 30 Liquid Equities..."):
        nifty = yf.download("^NSEI", period="3mo", interval="1d", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        nifty['EMA_50'] = nifty['Close'].ewm(span=50, adjust=False).mean()
        curr_nifty = round(float(nifty['Close'].iloc[-1]), 2)
        is_bullish = curr_nifty > float(nifty['EMA_50'].iloc[-1])
        nifty_1m = ((curr_nifty / float(nifty['Close'].iloc[-21])) - 1) * 100

        col1, col2, col3 = st.columns(3)
        col1.metric("Nifty 50 Level", f"₹{curr_nifty:,.2f}", f"{nifty_1m:+.2f}% (1M)")
        col2.metric("Macro Market Regime", "🟢 BULLISH" if is_bullish else "🔴 BEARISH")
        col3.metric("Scan Time (IST)", datetime.now().strftime("%d-%b %H:%M"))

        # Single Fast Batch Download (Prevents Yahoo Rate-Limit KeyError)
        all_data = yf.download(WATCHLIST, period="6mo", interval="1d", group_by="ticker", progress=False)

        results = []
        top_df = None
        top_name = ""
        best_score = -1

        for ticker in WATCHLIST:
            try:
                if ticker not in all_data.columns.get_level_values(0):
                    continue
                df = all_data[ticker].dropna().copy()
                if len(df) < 55:
                    continue
                df = compute_indicators(df)
                last = df.iloc[-1]

                price = round(float(last['Close']), 2)
                rsi = round(float(last['RSI']), 2)
                ema20, ema50 = float(last['EMA_20']), float(last['EMA_50'])
                macd, sig = float(last['MACD']), float(last['Signal_Line'])
                atr = float(last['ATR'])
                vol_r = round(float(last['Vol_Ratio']), 2)

                alpha = round((((price / float(df['Close'].iloc[-21])) - 1) * 100) - nifty_1m, 2)
                res_20d = round(float(df['High'].tail(20).max()), 2)
                sup_20d = round(float(df['Low'].tail(20).min()), 2)

                score = 0
                if price > ema20 > ema50: score += 30
                elif price > ema20: score += 15
                if 45 <= rsi <= 65: score += 20
                elif rsi < 35: score += 25
                if macd > sig: score += 20
                if vol_r > 1.15: score += 15
                if alpha > 2.0: score += 15

                if score >= 85:
                    grade, mult = "🔥 A+ GRADE", 1.0
                elif score >= 70:
                    grade, mult = "✅ A GRADE", 0.75
                elif score >= 55:
                    grade, mult = "👀 WATCHLIST", 0.0
                else:
                    grade, mult = "⏳ NEUTRAL", 0.0

                news = get_news_sentiment(ticker) if score >= 70 else "⚪ SKIPPED"
                if "NEGATIVE" in news and score >= 70:
                    grade, mult = "🚫 VETOED (NEG NEWS)", 0.0

                sl = round(max(price - (1.5 * atr), sup_20d * 0.99), 2)
                tgt = round(price + (3.0 * atr), 2)
                qty = int(((capital * risk_pct) * mult) / max(price - sl, 1))

                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Price (₹)": price,
                    "Score": score,
                    "Signal": grade,
                    "Alpha vs Nifty": f"{alpha:+.2f}%",
                    "Support (₹)": sup_20d,
                    "Resistance (₹)": res_20d,
                    "Stop Loss (₹)": sl,
                    "Target (₹)": tgt,
                    "Smart Qty": qty,
                    "News": news
                })

                if score >= 80 and "VETOED" not in grade:
                    send_telegram(f"🚨 *NSE AI ALERT: {ticker.replace('.NS', '')}*\n• Grade: {grade} ({score}/100)\n• Price: ₹{price} | SL: ₹{sl} | Target: ₹{tgt}\n• Qty: {qty}")

                if score > best_score:
                    best_score = score
                    top_df = df.copy()
                    top_name = ticker.replace(".NS", "")
            except Exception:
                pass

        if len(results) > 0:
            res_df = pd.DataFrame(results).sort_values(by="Score", ascending=False).reset_index(drop=True)
            st.subheader("📊 Live Quantitative Signal Matrix")
            st.dataframe(res_df, use_container_width=True)

            if top_df is not None:
                st.subheader(f"📈 Institutional Chart: {top_name} (Score: {best_score}/100)")
                plot_df = top_df.tail(90)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Price"), row=1, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_20'], line=dict(color='cyan', width=1.5), name="20 EMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_50'], line=dict(color='orange', width=1.5), name="50 EMA"), row=1, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI'], line=dict(color='violet', width=2), name="RSI"), row=2, col=1)
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Yahoo Finance server temporary busy hai. Kripya 10 second baad dobara 'Run Live NSE Quant Scan' button dabayein.")
