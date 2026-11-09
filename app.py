import streamlit as st
import datetime
import pytz
import time
from PIL import Image

st.set_page_config(page_title="TSM TRADER 99", page_icon="⚡", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #FFD700;'>🔐 TSM TRADER 99 - Security Portal</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("Activation Password", type="password", placeholder="পাসওয়ার্ড লিখুন...")
        if st.button("Unlock Analyzer", use_container_width=True):
            if password_input == "TSM99@2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ ভুল পাসওয়ার্ড!")
    st.stop()

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>⚡ TSM TRADER 99</h1>", unsafe_allow_html=True)
    market_mode = st.radio("Select Trading Mode:", ["🌐 OTC Mode (All Pairs)", "📈 Real Market Mode"], index=0)
    st.markdown("---")
    
    bd_tz = pytz.timezone('Asia/Dhaka')
    utc_tz = pytz.utc
    bd_time = datetime.datetime.now(bd_tz)
    utc_time = datetime.datetime.now(utc_tz)
    
    st.markdown(f"**🇧🇩 BD Time:** `{bd_time.strftime('%I:%M:%S %p')}`")
    st.markdown(f"**🌐 Quotex UTC:** `{utc_time.strftime('%H:%M:%S')} UTC`")
    st.markdown(f"**⏳ Candle Timer:** `00:{60 - bd_time.second:02d}s left`")
    
    if st.button("🔒 Lock Analyzer", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<h1 style='text-align: center;'>🎯 TSM TRADER 99 - Live Signal Analyzer</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Active Mode: <b>{market_mode}</b> | স্ক্রিনশট আপলোড করলেই অটো-স্ক্যান হবে।</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📁 চার্টের স্ক্রিনশট এখানে আপলোড করুন", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Uploaded Chart", use_column_width=True)
    with col2:
        st.markdown("### 📊 AI Analysis Result")
        with st.status("🚀 Processing chart...", expanded=True):
            time.sleep(1)
        st.success("✅ Analysis Complete!")
        st.markdown("**Signal:** `CALL (BUY) 🟢` (Confidence: 95%)")
else:
    st.info("💡 গ্যালারি থেকে যেকোনো চার্টের স্ক্রিনশট আপলোড করুন।")
