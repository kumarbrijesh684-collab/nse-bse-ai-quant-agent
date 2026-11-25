import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from textblob import TextBlob
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="QUANTDESK INDIA", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background: #06090F; color: #E2E8F0; }
    .hdr { background: #0D1321; border-left: 4px solid #00E599; padding: 16px 20px; border-radius: 10px; margin-bottom: 16px; }
    .hdr h2 { margin: 0; color: #F8FAFC; font-size: 20px; }
    .hdr p { margin: 4px 0 0 0; color: #94A3B8; font-size: 12px; }
    .ticket { background: #0D1525; border: 1px solid #1E293B; border-top: 3px solid #00E599; border-radius: 10px; padding: 14px; margin-bottom: 10px; }
    div.stButton > button:first-child { background: linear-gradient(90deg, #00C885, #0284C7); color: #040914; font-weight: 800; border: none; border-radius: 8px; width: 100%; padding: 12px; }
</style>
""", unsafe_allow_html=True)

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))

st.markdown(f"""
<div class="hdr">
    <h2>⚡ QUANTDESK <span style="color:#00E599;">INDIA</span> // NSE·BSE TERMINAL</h2>
    <p>ARCHITECT: BRIJESH KUMAR PATEL • v6.2 PRODUCTION • {ist_now.strftime('%d %b %Y %H:%M IST')}</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Desk Risk & Alerts")
capital = st.sidebar.number_input("Capital (₹)", min_value=10000, value=100000, step=10000)
risk_pct = st.sidebar.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0, 0.5) / 100
enable_tg = st.sidebar.checkbox("Enable Telegram Alerts", value=False)
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat_id = st.sidebar.text_input("Chat ID")

def send_tg(msg):
    if enable_tg and tg_token and tg_chat_id:
        try:
            requests.post(f"https://telegram.org{tg_token}/sendMessage", json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
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

def add_indicators(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    tr = np.max(pd.concat([df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift()), np.abs(df['Low'] - df['Close'].shift())], axis=1), axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    return df

def get_news(sym):
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

if "done" not in st.session_state:
    st.session_state.done = False

if st.button("⚡ EXECUTE QUANT SCAN"):
    with st.spinner("Scanning NSE Market Regime & 30 Liquid Equities..."):
        nifty = yf.download("^NSEI", period="3mo", interval="1d", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        nifty['EMA_50'] = nifty['Close'].ewm(span=50, adjust=False).mean()
        curr_n = round(float(nifty['Close'].iloc[-1]), 2)
        bullish = curr_n > float(nifty['EMA_50'].iloc[-1])
        n_1m = ((curr_n / float(nifty['Close'].iloc[-21])) - 1) * 100

        raw = yf.download(WATCHLIST, period="1y", interval="1d", group_by="ticker", progress=False)
        rows = []
        dfs = {}

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

                sc = 0
                if p > e20 > e50:
                    sc += 30
                elif p > e20:
                    sc += 15
                if 45 <= rsi <= 65:
                    sc += 20
                elif rsi < 35:
                    sc += 25
                if macd > sig:
                    sc += 20
                if vr > 1.15:
                    sc += 15
                if alpha > 2.0:
                    sc += 15

                if sc >= 85:
                    grade, mult = "A+ STRONG BUY", 1.0
                elif sc >= 70:
                    grade, mult = "A BUY SETUP", 0.75
                elif sc >= 55:
                    grade, mult = "WATCHLIST", 0.0
                else:
                    grade, mult = "NEUTRAL", 0.0

                news = get_news(t) if sc >= 70 else "SKIPPED"
                if "NEGATIVE" in news and sc >= 70:
                    grade, mult = "VETOED (NEWS)", 0.0

                sl = round(max(p - (1.5 * atr), sup20 * 0.99), 2)
                tgt = round(p + (3.0 * atr), 2)
                qty = int(((capital * risk_pct) * mult) / max(p - sl, 1))

                rows.append({
                    "Symbol": sym, "LTP (₹)": p, "Score": sc, "Signal": grade,
                    "Alpha (1M)": alpha, "RSI": rsi, "Support (₹)": sup20,
                    "Resistance (₹)": res20, "Stop Loss (₹)": sl, "Target (₹)": tgt,
                    "Qty": qty, "News": news
                })

                if sc >= 80 and "VETOED" not in grade:
                    send_tg(f"🚨 *QUANTDESK ALERT: {sym}*\n• {grade} ({sc}/100)\n• Entry: ₹{p} | SL: ₹{sl} | Target: ₹{tgt} | Qty: {qty}")
            except Exception:
                continue

        if rows:
            st.session_state.done = True
            st.session_state.df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
            st.session_state.dfs = dfs
            st.session_state.nifty = curr_n
            st.session_state.n_1m = n_1m
            st.session_state.bull = bullish
        else:
            st.warning("⚠️ Data feed busy. Wait 10 seconds and tap Execute Quant Scan again.")

if st.session_state.done:
    df_out = st.session_state.df
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NIFTY 50", f"₹{st.session_state.nifty:,.2f}", f"{st.session_state.n_1m:+.2f}%")
    c2.metric("REGIME", "BULLISH" if st.session_state.bull else "BEARISH")
    c3.metric("SETUPS (>=70)", f"{len(df_out[df_out['Score'] >= 70])} / {len(df_out)}")
    c4.metric("TOP ALPHA", df_out.iloc[0]['Symbol'], f"{df_out.iloc[0]['Alpha (1M)']:+.2f}%")

    st.markdown("#### 🎯 Priority Trade Tickets")
    cols = st.columns(3)
    for i in range(min(3, len(df_out))):
        r = df_out.iloc[i]
        with cols[i]:
            st.markdown(f"""
            <div class="ticket">
                <b style="font-size:17px; color:#FFF;">{r['Symbol']}</b> <span style="color:#00E599; font-size:12px;">[{r['Signal']} • {r['Score']}/100]</span><br>
                <span style="font-size:13px; color:#CBD5E1;">Entry: <b>₹{r['LTP (₹)']}</b> | Qty: <b>{r['Qty']}</b></span><br>
                <span style="font-size:13px; color:#F43F5E;">SL: <b>₹{r['Stop Loss (₹)']}</b></span> &nbsp;|&nbsp;
                <span style="font-size:13px; color:#00E599;">Target: <b>₹{r['Target (₹)']}</b></span>
            </div>
            """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📊 Screener Matrix", "📈 Chart Desk", "🧪 1-Yr Backtest"])

    with t1:
        st.dataframe(df_out, use_container_width=True, height=450)
        st.download_button("📥 Download CSV Report", df_out.to_csv(index=False).encode(), "QuantDesk_Signals.csv", "text/csv")

    with t2:
        pick = st.selectbox("Select Stock:", df_out["Symbol"].tolist())
        if pick in st.session_state.dfs:
            pdf = st.session_state.dfs[pick].tail(90)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=pdf.index, open=pdf['Open'], high=pdf['High'], low=pdf['Low'], close=pdf['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=pdf.index, y=pdf['EMA_20'], line=dict(color='#38BDF8', width=1.5), name="20 EMA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=pdf.index, y=pdf['EMA_50'], line=dict(color='#F59E0B', width=1.5), name="50 EMA"), row=1, col=1)
