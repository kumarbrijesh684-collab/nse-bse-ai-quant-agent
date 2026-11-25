import pandas as pd

def init_wallet(session_state, default_capital=100000.0):
    defaults = {
        "paper_cash": float(default_capital),
        "open_pos": [],
        "closed_pos": [],
        "done": False
    }
    for k, v in defaults.items():
        if k not in session_state:
            session_state[k] = v

def calculate_risk_order(row, capital, risk_pct):
    entry_p = float(row["LTP (₹)"])
    sl_p = float(row["Stop Loss (₹)"])
    tgt_p = float(row["Target (₹)"])
    risk_per_share = max(entry_p - sl_p, 1.0)
    max_risk_amt = round(capital * risk_pct, 2)
    safe_qty = max(1, int(max_risk_amt / risk_per_share))
    trade_val = round(safe_qty * entry_p, 2)
    actual_risk = round(safe_qty * risk_per_share, 2)
    return {
        "Symbol": row["Symbol"],
        "Entry": entry_p,
        "SL": sl_p,
        "Target": tgt_p,
        "Qty": safe_qty,
        "Value": trade_val,
        "MaxRisk": actual_risk
    }

def execute_buy_order(session_state, order_dict, max_trades, timestamp_str):
    if len(session_state.open_pos) >= max_trades:
        return False, f"Max {max_trades} open trades limit reached!"
    if order_dict["Value"] > session_state.paper_cash:
        return False, "Insufficient Cash in Paper Wallet!"
    if any(p["Symbol"] == order_dict["Symbol"] for p in session_state.open_pos):
        return False, f"{order_dict['Symbol']} is already open!"

    session_state.paper_cash = round(session_state.paper_cash - order_dict["Value"], 2)
    order_dict["Time"] = timestamp_str
    session_state.open_pos.append(order_dict)
    return True, f"Executed {order_dict['Symbol']} ({order_dict['Qty']} Qty @ ₹{order_dict['Entry']})"

def sync_auto_sl_target(session_state, live_price_map, timestamp_str):
    remaining = []
    for pos in session_state.open_pos:
        cp = live_price_map.get(pos["Symbol"], pos["Entry"])
        if cp <= pos["SL"] or cp >= pos["Target"]:
            status = "🏆 TARGET HIT" if cp >= pos["Target"] else "🛑 SL HIT"
            pnl = round((cp - pos["Entry"]) * pos["Qty"], 2)
            session_state.paper_cash = round(session_state.paper_cash + (cp * pos["Qty"]), 2)
            session_state.closed_pos.append({
                "Symbol": pos["Symbol"], "Qty": pos["Qty"], "Entry": pos["Entry"],
                "Exit": cp, "Status": status, "Net P&L (₹)": pnl, "Time": timestamp_str
            })
        else:
            remaining.append(pos)
    session_state.open_pos = remaining

def close_position_manually(session_state, idx, live_price_map, timestamp_str):
    pos = session_state.open_pos.pop(idx)
    cp = live_price_map.get(pos["Symbol"], pos["Entry"])
    pnl = round((cp - pos["Entry"]) * pos["Qty"], 2)
    session_state.paper_cash = round(session_state.paper_cash + (cp * pos["Qty"]), 2)
    session_state.closed_pos.append({
        "Symbol": pos["Symbol"], "Qty": pos["Qty"], "Entry": pos["Entry"],
        "Exit": cp, "Status": "MANUAL EXIT", "Net P&L (₹)": pnl, "Time": timestamp_str
    })
  
