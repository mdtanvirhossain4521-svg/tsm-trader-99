import datetime as dt
import os
import sqlite3
import uuid

import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
import yfinance as yf

APP_NAME = "TSM TRADER 99"
DB_FILE = "tsm_trader.db"
st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")
st.markdown("""<style>.block-container{max-width:1100px;padding-top:1rem}.signal{font-size:30px;font-weight:800}</style>""", unsafe_allow_html=True)


def secret(name):
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, "")


def db():
    con = sqlite3.connect(DB_FILE, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS signals(
        id TEXT PRIMARY KEY, created_at TEXT, symbol TEXT, timeframe TEXT,
        direction TEXT, score REAL, entry REAL, explanation TEXT,
        outcome TEXT DEFAULT 'Pending')""")
    con.commit()
    return con


def history():
    con = db()
    result = pd.read_sql_query("SELECT * FROM signals ORDER BY created_at DESC LIMIT 30", con)
    con.close()
    return result


def save_signal(symbol, timeframe, direction, score, price, explanation):
    con = db()
    con.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?,?,?)", (
        str(uuid.uuid4()), dt.datetime.now(pytz.utc).isoformat(), symbol,
        timeframe, direction, score, price, explanation, "Pending"))
    con.commit()
    con.close()


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def indicators(frame):
    frame = frame.copy()
    close = frame["Close"]
    frame["EMA20"] = ema(close, 20)
    frame["EMA50"] = ema(close, 50)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    frame["RSI"] = 100 - 100 / (1 + rs)
    macd = ema(close, 12) - ema(close, 26)
    frame["MACD"] = macd
    frame["MACD_SIGNAL"] = ema(macd, 9)
    return frame


def fetch(symbol, interval, period):
    raw = yf.download(symbol, period=period, interval=interval, auto_adjust=True,
                      progress=False, threads=False)
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    required = ["Open", "High", "Low", "Close"]
    if not all(name in raw.columns for name in required):
        return pd.DataFrame()
    frame = raw[required].dropna().copy()
    frame.index = pd.to_datetime(frame.index, utc=True)
    return frame


def decide(frame):
    if len(frame) < 60:
        return "WAIT", 0, "Not enough candles to calculate indicators.", frame
    frame = indicators(frame)
    row = frame.iloc[-1]
    up = int(row.EMA20 > row.EMA50) + int(row.MACD > row.MACD_SIGNAL) + int(row.RSI >= 55)
    down = int(row.EMA20 < row.EMA50) + int(row.MACD < row.MACD_SIGNAL) + int(row.RSI <= 45)
    if up == 3:
        direction = "CALL"
    elif down == 3:
        direction = "PUT"
    else:
        direction = "WAIT"
    score = round(max(up, down) / 3 * 100, 1)
    reason = f"EMA20/50 trend; RSI {row.RSI:.1f}; MACD {'bullish' if row.MACD > row.MACD_SIGNAL else 'bearish'}"
    return direction, score, reason, frame


# Login passwords are set in Streamlit Cloud app settings > Secrets.
admin_password = secret("ADMIN_PASSWORD")
user_password = secret("USER_PASSWORD")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.authenticated:
    st.title("🔐 TSM TRADER 99")
    if not admin_password and not user_password:
        st.warning("প্রথমে Streamlit Cloud → App settings → Secrets-এ ADMIN_PASSWORD এবং USER_PASSWORD যোগ করুন।")
        st.code('ADMIN_PASSWORD = "একটি-শক্তিশালী-পাসওয়ার্ড"\nUSER_PASSWORD = "ব্যবহারকারীর-পাসওয়ার্ড"', language="toml")
    else:
        entered = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if admin_password and entered == admin_password:
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.rerun()
            elif user_password and entered == user_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("পাসওয়ার্ড সঠিক নয়।")
    st.stop()

left, right = st.columns([4, 1])
left.title("📈 TSM TRADER 99")
if right.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.rerun()

bd = dt.datetime.now(pytz.timezone("Asia/Dhaka"))
utc_now = dt.datetime.now(pytz.utc)
a, b, c = st.columns(3)
a.metric("বাংলাদেশ সময়", bd.strftime("%I:%M:%S %p"))
b.metric("UTC", utc_now.strftime("%H:%M:%S"))
c.metric("পরের মিনিটে", f"00:{60-bd.second:02d}")
st.caption("শিক্ষামূলক বিশ্লেষণ—এটি আর্থিক পরামর্শ নয়, লাভ/সঠিকতার নিশ্চয়তা দেয় না এবং কোনো ট্রেড চালায় না।")

symbols = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X", "Gold futures": "GC=F", "BTC/USD": "BTC-USD"}
timeframes = {"5m": ("5m", "30d"), "15m": ("15m", "60d"), "1h": ("1h", "730d")}
col1, col2 = st.columns(2)
market = col1.selectbox("Market", list(symbols))
timeframe = col2.selectbox("Timeframe", list(timeframes), index=0)

if st.button("Fetch data and analyze", type="primary", use_container_width=True):
    st.session_state.pop("analysis", None)
    try:
        with st.spinner("Fetching public market data…"):
            candles = fetch(symbols[market], *timeframes[timeframe])
        if candles.empty:
            st.error("এই মুহূর্তে public feed থেকে ডেটা পাওয়া যায়নি।")
        else:
            direction, score, reason, analyzed = decide(candles)
            st.session_state.analysis = (market, timeframe, direction, score, reason, analyzed)
    except Exception as exc:
        st.error(f"ডেটা আনতে সমস্যা হয়েছে: {type(exc).__name__}")

analysis = st.session_state.get("analysis")
if analysis:
    market, timeframe, direction, score, reason, frame = analysis
    latest = frame.iloc[-1]
    price = float(latest.Close)
    x, y, z = st.columns(3)
    x.metric("সর্বশেষ মূল্য", f"{price:.5f}")
    y.metric("RSI (14)", f"{latest.RSI:.1f}")
    z.metric("Indicator agreement", f"{score:.0f}/100")
    color = "#00C853" if direction == "CALL" else "#FF5252" if direction == "PUT" else "#FFD740"
    st.markdown(f"<div class='signal' style='color:{color}'>{direction}</div>", unsafe_allow_html=True)
    st.write(reason)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=frame.index, open=frame.Open, high=frame.High, low=frame.Low, close=frame.Close, name="Price"))
    fig.add_trace(go.Scatter(x=frame.index, y=frame.EMA20, name="EMA20"))
    fig.add_trace(go.Scatter(x=frame.index, y=frame.EMA50, name="EMA50"))
    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    if st.button("Save signal to history"):
        save_signal(market, timeframe, direction, score, price, reason)
        st.success("Signal saved.")

st.divider()
st.subheader("Signal history")
records = history()
if records.empty:
    st.info("এখনও কোনো সিগন্যাল সংরক্ষিত হয়নি।")
else:
    st.dataframe(records[["created_at", "symbol", "timeframe", "direction", "score", "entry", "outcome"]], use_container_width=True, hide_index=True)

st.caption("দাম/ডেটা Yahoo Finance-এর public feed থেকে; এটি Quotex OTC feed নয়। OTC chart-এর ডেটা এতে দেখানো হবে না।")
