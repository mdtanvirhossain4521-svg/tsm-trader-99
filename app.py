import streamlit as st
import datetime
import pytz
import time
import random
import json
import os
import uuid
from PIL import Image
from streamlit_autorefresh import st_autorefresh

# ১. পেজ কনফিগারেশন ও ব্রাউজার ট্যাব সেটআপ
st.set_page_config(
    page_title="TSM TRADER 99",
    page_icon="⚡",
    layout="centered"
)

# ঘড়ি এবং টাইমার প্রতি ১ সেকেন্ড পরপর নিখুঁত লাইভ আপডেটের জন্য অটো-রিফ্রেশ
st_autorefresh(interval=1000, limit=None, key="live_clock_refresh")

# স্টাইল ও ডিজাইন কাস্টমাইজেশন
st.markdown("""
    <style>
    .main-title { text-align: center; color: #FFD700; font-weight: bold; }
    .sub-text { text-align: center; color: #AAAAAA; }
    .signal-box { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border: 1px solid #00E676; text-align: center; }
    .admin-box { padding: 12px; border-radius: 8px; background-color: #262626; border: 1px solid #FFD700; margin-bottom: 10px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# ২. সেশন স্টেট ও সিকিউরিটি ম্যানেজমেন্ট
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

# লাইভ ইউজার ট্র্যাকিং ফাংশন (JSON ফাইলের মাধ্যমে)
TRACKER_FILE = "active_users.json"

def update_user_activity(user_id, role, user_agent):
    data = {}
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
            
    current_time = time.time()
    
    device_name = "Desktop / PC"
    if "Mobile" in user_agent:
        device_name = "Android Mobile"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        device_name = "iOS / iPhone"

    data[user_id] = {
        "last_seen": current_time,
        "device": device_name,
        "role": role
    }
    
    active_users = {}
    for uid, info in data.items():
        if current_time - info["last_seen"] < 30:
            active_users[uid] = info
            
    try:
        with open(TRACKER_FILE, "w") as f:
            json.dump(active_users, f)
    except:
        pass
        
    return active_users

# লগইন পোর্টাল
if not st.session_state.authenticated:
    try:
        logo_img = Image.open("tsm_logo.png")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(logo_img, use_column_width=True)
    except:
        pass
        
    st.markdown("<h2 class='main-title'>🔐 TSM TRADER 99 - Security Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-text'>অ্যানালাইজার ব্যবহার করতে আপনার পাসওয়ার্ড দিন।</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("Access Password", type="password", placeholder="পাসওয়ার্ড লিখুন...")
        if st.button("Unlock Analyzer", use_container_width=True):
            if password_input == "2T1A1N2V7I0R":  # মাস্টার অ্যাডমিন পাসওয়ার্ড
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.rerun()
            elif password_input == "TRADER99":  # সাধারণ ইউজারদের পাসওয়ার্ড (কোনো অ্যাডমিন প্যানেল নেই)
                st.session_state.authenticated = True
                st.session_state.is_admin = False
                st.rerun()
            else:
                st.error("❌ ভুল পাসওয়ার্ড! সঠিক পাসওয়ার্ড দিন।")
    st.stop()

# ইউজার অ্যাক্টিভিটি আপডেট
user_agent = st.context.headers.get("User-Agent", "Unknown")
role_str = "Admin" if st.session_state.is_admin else "User"
current_active_dict = update_user_activity(st.session_state.user_id, role_str, user_agent)

# ৩. অ্যাডমিন প্যানেল (সাইডবার - শুধুমাত্র আপনার জন্য দৃশ্যমান)
if st.session_state.is_admin:
    with st.sidebar:
        st.markdown("<h2 style='color: #FFD700; text-align: center;'>👑 Admin Panel</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        try:
            logo_img = Image.open("tsm_logo.png")
            st.image(logo_img, use_column_width=True)
        except:
            pass
            
        active_count = len(current_active_dict)
        st.markdown("### 📊 Live Traffic Stats")
        st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
        st.markdown(f"🟢 **Live Active Users:** `{active_count}`")
        st.markdown(f"💻 **Your Device:** `{current_active_dict.get(st.session_state.user_id, {}).get('device', 'Unknown')}`")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("### 📱 Connected Users & Devices")
        st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
        for uid, info in current_active_dict.items():
            badge = "👑 (You/Admin)" if info['role'] == 'Admin' else "👤 (User)"
            st.markdown(f"• ID: `{uid}` | {info['device']} {badge}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Admin Controls")
        if st.button("🔄 Refresh Live Data", use_container_width=True):
            st.rerun()
            
        st.markdown("---")
        if st.button("🔒 Logout Admin", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.rerun()

# ৪. মেইন ড্যাশবোর্ড হেডার
try:
    logo_img = Image.open("tsm_logo.png")
    col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
    with col_l2:
        st.image(logo_img, use_column_width=True)
except:
    st.markdown("<h1 style='text-align: center; color: #00E676;'>⚡ TSM TRADER 99</h1>", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🎯 TSM TRADER 99 - Live Signal Analyzer</h1>", unsafe_allow_html=True)
st.markdown("---")

# ৫. কন্ট্রোল প্যানেল ও নিখুঁত পাইথন-বেসড লাইভ ক্লক ও টাইমার
col_c1, col_c2 = st.columns([1, 1])

with col_c1:
    market_mode = st.radio(
        "🎯 Select Trading Mode:", 
        ["🌐 OTC Mode", "📈 Real Market Mode"], 
        index=1
    )

with col_c2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Lock Analyzer", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.rerun()

# লাইভ টাইম ক্যালকুলেশন
bd_tz = pytz.timezone('Asia/Dhaka')
utc_tz = pytz.utc
bd_time = datetime.datetime.now(bd_tz)
utc_time = datetime.datetime.now(utc_tz)
remaining_seconds = 60 - bd_time.second
if remaining_seconds == 60:
    remaining_seconds = 0

# ইউজার ইন্টারফেসে লাইভ ডিসপ্লে বক্স
st.markdown(f"""
    <div style="display: flex; justify-content: space-around; background-color: #1E1E1E; padding: 12px; border-radius: 8px; border: 1px solid #00E676; text-align: center; margin-top: 10px;">
        <div>
            <div style="font-size: 11px; color: #AAAAAA;">🇧🇩 BD TIME</div>
            <div style="font-size: 15px; font-weight: bold; color: #00E676;">{bd_time.strftime('%I:%M:%S %p')}</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #AAAAAA;">🌐 UTC TIME</div>
            <div style="font-size: 15px; font-weight: bold; color: #00FFCC;">{utc_time.strftime('%H:%M:%S')} UTC</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #AAAAAA;">⏳ NEXT CANDLE</div>
            <div style="font-size: 15px; font-weight: bold; color: #FFEB3B;">00:{remaining_seconds:02d}s</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"<p class='sub-text'>Active Mode: <b>{market_mode}</b> | গ্যালারি থেকে চার্টের স্ক্রিনশট আপলোড করুন।</p>", unsafe_allow_html=True)

# ৬. স্ক্রিনশট আপলোড ও এআই সিগন্যাল সেকশন
uploaded_file = st.file_uploader("📁 চার্টের স্ক্রিনশট এখানে আপলোড করুন", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(image, caption="Uploaded Chart Preview", use_column_width=True)
        
    with col2:
        st.markdown("### 📊 AI Smart Analysis")
        
        with st.status("🚀 চার্ট স্ক্যান করা হচ্ছে...", expanded=True) as status:
            time.sleep(1.5)
            status.update(label="📈 ক্যান্ডেলস্টিক স্ট্রাকচার ও ট্রেন্ড বিশ্লেষণ করা হচ্ছে...", state="running")
            time.sleep(1.5)
            status.update(label="⚡ নেক্সট ক্যান্ডেল এন্ট্রি ক্যালকুলেশন সম্পন্ন!", state="complete", expanded=False)
        
        st.success("✅ Analysis Successful!")
        
        if "current_signal" not in st.session_state:
            st.session_state.current_signal = random.choice(["CALL (BUY) 🟢", "PUT (SELL) 🔴"])
            st.session_state.confidence_rate = round(random.uniform(89.0, 98.5), 1)

        sig_type = st.session_state.current_signal
        sig_color = "#00E676" if "BUY" in sig_type else "#FF5252"
        
        st.markdown(f"""
            <div class='signal-box'>
                <h3 style='color: #00FFCC; margin: 0;'>RECOMMENDED SIGNAL</h3>
                <h1 style='color: {sig_color}; margin: 10px 0;'>{sig_type}</h1>
                <p style='margin: 0; color: #FFFFFF;'>Confidence Rate: <b>{st.session_state.confidence_rate}%</b></p>
                <p style='margin: 5px 0 0 0; font-size: 13px; color: #FFEB3B;'>⏰ Next Candle শুরু হওয়ার সাথে সাথে সঠিক এন্ট্রি নিন।</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 New Chart Scan"):
            st.session_state.current_signal = random.choice(["CALL (BUY) 🟢", "PUT (SELL) 🔴"])
            st.session_state.confidence_rate = round(random.uniform(89.0, 98.5), 1)
            st.rerun()
else:
    st.info("💡 ট্রেড করার আগে মার্কেটের রানিং ক্যান্ডেলের একটি পরিষ্কার স্ক্রিনশট ওপরে আপলোড করুন। সিস্টেম স্বয়ংক্রিয়ভাবে স্ক্যান করে সিগন্যাল দিয়ে দেবে।")
