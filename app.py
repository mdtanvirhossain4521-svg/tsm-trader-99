import streamlit as st
import datetime as dt
import os
import sqlite3
import uuid

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytz
import yfinance as yf

APP_NAME = "TSM TRADER 99"
DB_FILE = "tsm_trader.db"

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; max-width: 1180px;}
.metric-card {background:#111827;border:1px solid #263244;border-radius:12px;padding:14px;margin:6px 0}
.buy {color:#00E676;font-weight:800;font-size:28px}
.sell {color:#FF5252;font-weight:800;font-size:28px}
.wait {color:#FFD54F;font-weight:800;font-size:28px}
.small {color:#9CA3AF;font-size:13px}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Database
# -----------------------------
def db():
    con = sqlite3.connect(DB_FILE, check_same_thread=False)
    con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            symbol TEXT,
            timeframe TEXT,
            direction TEXT,
            score REAL,
            entry REAL,
            explanation TEXT,
            outcome TEXT DEFAULT 'Pending'
        )
    """)
    con.commit()
    return con


def save_signal(symbol, timeframe, direction, score, entry, explanation):
    con = db()
    con.execute(
        "INSERT INTO signals VALUES (?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), dt.datetime.now(pytz.utc).isoformat(), symbol,
         timeframe, direction, score, entry, explanation, "Pending"),
    )
    con.commit()
    con.close()


def signal_history(limit=20):
    con = db()
    df = pd.read_sql_query(
        "SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", con, params=(limit,)
    )
    con.close()
    return df


def set_outcome(signal_id, outcome):
    con = db()
    con.execute("UPDATE signals SET outcome=? WHERE id=?", (outcome, signal_id))
    con.commit()
    con.close()

# -----------------------------
# Authentication
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
USER_PASSWORD = os.getenv("USER_PASSWORD", "")

if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("## 🔐 TSM TRADER 99")
        st.caption("Authorized access only")
        password = st.text_input("Password", type="password")
        if st.button("Open dashboard", use_container_width=True):
            if ADMIN_PASSWORD and password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.rerun()
            elif USER_PASSWORD and password == USER_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.is_admin = False
                st.rerun()
            else:
                st.error("Invalid password or passwords are not configured.")
        st.info("Set ADMIN_PASSWORD and USER_PASSWORD in Streamlit Secrets, not in source code.")
    st.stop()

# -----------------------------
# Technical indicators
# -----------------------------
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    average_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series):
    fast = ema(series, 12)
    slow = ema(series, 26)
    line = fast - slow
    signal = line.ewm(span=9, adjust=False).mean()
    return line, signal


def atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def normalize_yf_frame(raw):
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    needed = ["Open", "High", "Low", "Close"]
    if not all(c in raw.columns for c in needed):
        return pd.DataFrame()
    frame = raw[needed].dropna().copy()
    frame.index = pd.to_datetime(frame.index, utc=True)
    return frame


def fetch_market(symbol, interval, period):
    raw = yf.download(symbol, period=period, interval=interval,
                      auto_adjust=True, progress=False, threads=False)
    return normalize_yf_frame(raw)


def generate_signal(frame):
    if len(frame) < 60:
        return "WAIT", 0, "Not enough valid market data.", frame

    close = frame["Close"]
    frame = frame.copy()
    frame["EMA20"] = ema(close, 20)
    frame["EMA50"] = ema(close, 50)
    frame["RSI"] = rsi(close, 14)
    frame["MACD"], frame["MACD_SIGNAL"] = macd(close)
    frame["ATR"] = atr(frame["High"], frame["Low"], close, 14)

    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    bullish = 0
    bearish = 0

    if latest["EMA20"] > latest["EMA50"]:
        bullish += 1
    else:
        bearish += 1

    if latest["RSI"] >= 55:
        bullish += 1
    elif latest["RSI"] <= 45:
        bearish += 1

    if latest["MACD"] > latest["MACD_SIGNAL"]:
        bullish += 1
    else:
        bearish += 1

    if latest["Close"] > previous["Close"]:
        bullish += 1
    else:
        bearish += 1

    if bullish >= 3 and bullish > bearish:
        direction = "CALL"
        score = round(50 + bullish * 10, 1)
    elif bearish >= 3 and bearish > bullish:
        direction = "PUT"
        score = round(50 + bearish * 10, 1)
    else:
        direction = "WAIT"
        score = round(50 + max(bullish, bearish) * 5, 1)

    reasons = [
        f"EMA20 {'above' if latest['EMA20'] > latest['EMA50'] else 'below'} EMA50",
        f"RSI {latest['RSI']:.1f}",
        f"MACD {'above' if latest['MACD'] > latest['MACD_SIGNAL'] else 'below'} its signal",
    ]
    explanation = " | ".join(reasons)
    return direction, min(score, 90), explanation, frame

# -----------------------------
# Dashboard
# -----------------------------
bd = pytz.timezone("Asia/Dhaka")
utc = pytz.utc
now_bd = dt.datetime.now(bd)
now_utc = dt.datetime.now(utc)
remaining = 60 - now_bd.second
remaining = 60 if remaining == 60 else remaining

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown(f"# 📈 {APP_NAME}")
with header_right:
    if st.button("🔒 Lock", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.rerun()

m1, m2, m3 = st.columns(3)
m1.metric("🇧🇩 Bangladesh", now_bd.strftime("%I:%M:%S %p"))
m2.metric("🌐 UTC", now_utc.strftime("%H:%M:%S") + " UTC")
m3.metric("⏳ Next minute", f"00:{remaining:02d}s")

st.caption("Educational market-analysis tool. This is not financial advice and does not guarantee profit.")

symbols = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "XAU/USD": "GC=F",
    "BTC/USD": "BTC-USD",
}

left, right = st.columns([2, 2])
with left:
    market_name = st.selectbox("Market", list(symbols), index=0)
with right:
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h"], index=1)

interval_period = {
    ("1m"): ("1m", "7d"),
    ("5m"): ("5m", "30d"),
    ("15m"): ("15m", "60d"),
    ("1h"): ("1h", "730d"),
}
interval, period = interval_period[timeframe]

try:
    frame = fetch_market(symbols[market_name], interval, period)
    if frame.empty:
        st.error("Market data is unavailable. Check internet access or try another market/timeframe.")
        st.stop()

    direction, score, explanation, analyzed = generate_signal(frame)

    latest = analyzed.iloc[-1]
    previous = analyzed.iloc[-2]
    price = float(latest["Close"])
    change = float(latest["Close"] - previous["Close"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest price", f"{price:.5f}", f"{change:+.5f}")
    c2.metric("RSI (14)", f"{latest['RSI']:.1f}")
    c3.metric("ATR (14)", f"{latest['ATR']:.5f}" if pd.notna(latest["ATR"]) else "—")

    css = "buy" if direction == "CALL" else ("sell" if direction == "PUT" else "wait")
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='{css}'>{direction}</div>", unsafe_allow_html=True)
    st.markdown(f"**Strategy agreement:** {score:.1f}/100")
    st.markdown(f"<span class='small'>{explanation}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=analyzed.index,
        open=analyzed["Open"], high=analyzed["High"],
        low=analyzed["Low"], close=analyzed["Close"], name="Price",
    ))
    fig.add_trace(go.Scatter(x=analyzed.index, y=analyzed["EMA20"],
                             name="EMA20", line=dict(color="#00D4FF", width=1)))
    fig.add_trace(go.Scatter(x=analyzed.index, y=analyzed["EMA50"],
                             name="EMA50", line=dict(color="#FFB300", width=1)))
    fig.update_layout(template="plotly_dark", height=520, margin=dict(l=10,r=10,t=35,b=10),
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Save this signal", use_container_width=True):
        save_signal(market_name, timeframe, direction, score, price, explanation)
        st.success("Signal saved.")

except Exception as exc:
    st.error(f"Unable to analyze market data: {type(exc).__name__}")

st.markdown("---")
st.markdown("## 📋 Signal history")
history = signal_history()
if history.empty:
    st.info("No saved signals yet.")
else:
    for _, row in history.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
            c1.write(row["created_at"][:19].replace("T", " "))
            c2.write(f"{row['symbol']} · {row['timeframe']}")
            c3.write(f"{row['direction']} · {row['score']:.1f}")
            c4.write(row["outcome"])
            if row["outcome"] == "Pending":
                b1, b2 = c1.columns(2)
                if b1.button("WIN", key="win_" + row["id"]):
                    set_outcome(row["id"], "WIN")
                    st.rerun()
                if b2.button("LOSS", key="loss_" + row["id"]):
                    set_outcome(row["id"], "LOSS")
                    st.rerun()

if st.session_state.is_admin:
    with st.expander("Administrator"):
        st.write(f"Saved signals: {len(history)}")
        if st.button("Reset signal history"):
            con = db()
            con.execute("DELETE FROM signals")
            con.commit()
            con.close()
            st.rerun()

st.caption("Market feeds may be delayed. OTC instruments are not represented unless a licensed, authorized feed is configured.")
