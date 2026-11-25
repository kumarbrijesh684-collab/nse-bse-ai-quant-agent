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

# ==============================================================================
# 1. PAGE CONFIG & INSTITUTIONAL FINTECH DESIGN SYSTEM (CSS)
# ==============================================================================
st.set_page_config(
    page_title="QUANTDESK INDIA | NSE/BSE Algorithmic Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://googleapis.com');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #06090F;
        color: #E2E8F0;
    }

    .stApp {
        background: radial-gradient(circle at 15% 10%, #0D1526 0%, #06090F 55%, #04060A 100%);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        background: rgba(13, 19, 33, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-left: 4px solid #00E599;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 18px;
    }
    .brand-title {
        font-size: 21px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #F8FAFC;
        margin: 0;
    }
    .brand-accent { color: #00E599; }
    .brand-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 3px;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-pill {
        background: rgba(0, 229, 153, 0.12);
        border: 1px solid rgba(0, 229, 153, 0.4);
        color: #00E599;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    div[data-testid="metric-container"] {
        background: #0B111E;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px 16px;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px !important;
        font-weight: 700;
        color: #F8FAFC;
    }

    .trade-ticket {
        background: linear-gradient(145deg, #0D1525 0%, #090E1A 100%);
        border: 1px solid #1E293B;
        border-top: 3px solid #00E599;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .ticket-symbol {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .ticket-badge {
        background: rgba(0, 229, 153, 0.15);
        color: #00E599;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .ticket-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        font-size: 13px;
    }
    .t-label { color: #64748B; font-size: 11px; text-transform: uppercase; }
    .t-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #E2E8F0; }
    .t-sl { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #F43F5E; }
    .t-tgt { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #00E599; }

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00C885 0%, #0284C7 100%);
        color: #040914;
        font-weight: 800;
        letter-spacing: 0.4px;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        text-transform: uppercase;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
is_weekday = ist_now.weekday() < 5
market_open = is_weekday and (9 <= ist_now.hour < 15 or (ist_now.hour == 15 and ist_now.minute <= 30))
session_badge = "● NSE LIVE SESSION" if market_open else "○ NSE POST-MARKET"

st.markdown(f"""
<div class="terminal-header">
    <div>
        <div class="brand-title">QUANTDESK <span class="brand-accent">INDIA</span> // NSE·BSE TERMINAL</div>
        <div class="brand-sub">ARCHITECT: BRIJESH KUMAR PATEL | ENGINE: v6.1 MULTI-FACTOR + NLP VETO</div>
    </div>
    <div class="status-pill">{session_badge} • {ist_now.strftime('%d %b %H:%M IST')}</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR RISK & TELEGRAM CONTROLS
# ==============================================================================
st.sidebar.markdown("### ⚙️ Desk Risk Parameters")
capital = st.sidebar.number_input("Allocated Capital (₹)", min_value=10000, value=100000, step=10000)
risk_pct = st.sidebar.slider("Max Risk Per Trade (%)", 0.5, 5.0, 2.0, 0.5) / 100

st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 Telegram Bot Dispatch")
enable_tg = st.sidebar.checkbox("Enable Auto-Alerts", value=False)
tg_token = st.sidebar.text_input("Bot HTTP Token", type="password", placeholder="123456:ABC-DEF...")
tg_chat_id = st.sidebar.text_input("Chat ID", placeholder="987654321")

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

# ==============================================================================
# 3. QUANTITATIVE COMPUTATION ENGINE
# ==============================================================================
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
        if avg > 0.05:
            return "🟢 POSITIVE"
        elif avg < -0.05:
            return "🔴 NEGATIVE"
    except Exception:
        pass
    return "🟡 NEUTRAL"

if "scan_done" not in st.session_state:
    st.session_state.scan_done = False

col_btn, col_info = st.columns([1, 2])
with col_btn:
    run_clicked = st.button("⚡ EXECUTE QUANT SCAN")
with col_info:
    st.markdown(f"<div style='padding-top:10px; font-size:13px; color:#94A3B8;'>Universe: <b>30 Liquid NSE Equities</b> • Capital: <b>₹{capital:,}</b> • Max Risk/Trade: <b>{risk_pct*100:.1f}%</b></div>", unsafe_allow_html=True)

if run_clicked:
    with st.spinner("Running Multi-Factor Quant Matrix, Alpha Relative Strength & NLP News Gatekeeper..."):
        nifty = yf.download("^NSEI", period="3mo", interval="1d", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        nifty['EMA_50'] = nifty['Close'].ewm(span=50, adjust=False).mean()
        curr_nifty = round(float(nifty['Close'].iloc[-1]), 2)
        is_bullish = curr_nifty > float(nifty['EMA_50'].iloc[-1])
        nifty_1m = ((curr_nifty / float(nifty['Close'].iloc[-21])) - 1) * 100

        all_data = yf.download(WATCHLIST, period="1y", interval="1d", group_by="ticker", progress=False)

        results = []
        stock_dfs = {}

        for ticker in WATCHLIST:
            try:
                if ticker not in all_data.columns.get_level_values(0):
                    continue
                df = all_data[ticker].dropna().copy()
                if len(df) < 55:
                    continue
                df = compute_indicators(df)
                clean_sym = ticker.replace(".NS", "")
                stock_dfs[clean_sym] = df
                last = df.iloc[-1]

                price = round(float(last['Close']), 2)
                rsi = round(float(last['RSI']), 2)
                ema20, ema50 = float(last['EMA_20']), float(last['EMA_50'])
