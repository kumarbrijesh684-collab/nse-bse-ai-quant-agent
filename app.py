import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta
from quant_engine import run_quant_scan  # <-- Direct Backend Connection!

st.set_page_config(page_title="QUANTDESK INDIA", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{background:#06090F;color:#E2E8F0;} .hdr{background:#0D1321;border-left:4px solid #00E599;padding:15px;border-radius:10px;margin-bottom:15px;} div.stButton>button:first-child{background:linear-gradient(90deg,#00C885,#0284C7);color:#040914;font-weight:800;border:none;border-radius:8px;width:100%;padding:12px;}</style>", unsafe_allow_html=True)

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
st.markdown(f"<div class='hdr'><h3 style='margin:0;color:#FFF;'>⚡ QUANTDESK <span style='color:#00E599;'>INDIA</span> // MODULAR ALGO TERMINAL</h3><small style='color:#94A3B8;'>ARCHITECT: BRIJESH KUMAR PATEL • BACKEND: quant_engine.py • {ist_now.strftime('%d %b %H:%M IST')}</small></div>", unsafe_allow_html=True)

for k, v in [("paper_cash", 100000.0), ("open_pos", []), ("closed_pos", []), ("done", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

st.sidebar.header("⚙️ Settings & Alerts")
capital = st.sidebar.number_input("Capital (₹)", 10000, 10000000, 100000, 10000)
risk_pct = st.sidebar.slider("Risk/Trade (%)", 0.5, 5.0, 2.0, 0.5) / 100
tg_token = st.sidebar.text_input("Telegram Bot Token", type="password")
tg_chat = st.sidebar.text_input("Telegram Chat ID")

if st.button("⚡ EXECUTE QUANT ENGINE"):
    with st.spinner("Running quant_engine.py backend..."):
        df_res, dfs, nifty, n_1m, bull = run_quant_scan(capital, risk_pct, tg_token, tg_chat)
        if not df_res.empty:
            st.session_state.update({"done": True, "df": df_res, "dfs": dfs, "nifty": nifty, "n_1m": n_1m, "bull": bull})
        else:
            st.warning("⚠️ Data feed busy. Retry in 10 seconds.")

if st.session_state.done:
    df_out = st.session_state.df
    pmap = dict(zip(df_out["Symbol"], df_out["LTP (₹)"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NIFTY 50", f"₹{st.session_state.nifty:,.2f}", f"{st.session_state.n_1m:+.2f}%")
    c2.metric("REGIME", "BULLISH" if st.session_state.bull else "BEARISH")
    c3.metric("SETUPS (>=70)", f"{len(df_out[df_out['Score'] >= 70])}")
    c4.metric("PAPER WALLET", f"₹{st.session_state.paper_cash:,.2f}", f"{len(st.session_state.open_pos)} Open")

    t1, t2, t3 = st.tabs(["📊 Live Signals", "💼 Paper Trading", "📈 Chart Desk"])

    with t1:
        st.dataframe(df_out, use_container_width=True, height=430)
        st.download_button("📥 Download CSV", df_out.to_csv(index=False).encode(), "Signals.csv", "text/csv")

    with t2:
        sym = st.selectbox("Select Stock:", df_out["Symbol"].tolist())
        info = df_out[df_out["Symbol"] == sym].iloc
        qty = st.number_input("Qty:", 1, 10000, max(1, int(info["Qty"])))
        cost = round(float(info["LTP (₹)"]) * qty, 2)
        if st.button(f"🟢 PAPER BUY {sym} (₹{cost:,.2f})"):
            if cost <= st.session_state.paper_cash:
                st.session_state.paper_cash -= cost
                st.session_state.open_pos.append({"Symbol": sym, "Qty": qty, "Entry": float(info["LTP (₹)"]), "SL": float(info["Stop Loss (₹)"]), "Target": float(info["Target (₹)"])})
                st.rerun()
        for i, pos in enumerate(st.session_state.open_pos):
            cp = pmap.get(pos["Symbol"], pos["Entry"])
            pnl = round((cp - pos["Entry"]) * pos["Qty"], 2)
            col1, col2 = st.columns()
            col1.write(f"**{pos['Symbol']}** ({pos['Qty']} Qty) | Entry: ₹{pos['Entry']} → LTP: ₹{cp} | **P&L: ₹{pnl:+,.2f}**")
            if col2.button("Exit Trade", key=f"ex_{i}"):
                st.session_state.paper_cash += round(cp * pos["Qty"], 2)
                st.session_state.open_pos.pop(i)
                st.rerun()

    with t3:
        pick = st.selectbox("Inspect Chart:", df_out["Symbol"].tolist())
        if pick in st.session_state.dfs:
            pdf = st.session_state.dfs[pick].tail(90)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=pdf.index, open=pdf['Open'], high=pdf['High'], low=pdf['Low'], close=pdf['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=pdf.index, y=pdf['EMA_20'], line=dict(color='#38BDF8'), name="20 EMA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=pdf.index, y=pdf['RSI'], line=dict(color='#A78BFA'), name="RSI"), row=2, col=1)
            fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👆 Tap **⚡ EXECUTE QUANT ENGINE** to run `quant_engine.py`.")
