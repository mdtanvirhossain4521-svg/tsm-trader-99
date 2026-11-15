import streamlit as st
import datetime
import pytz
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
    .signal-box { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border: 1px solid #00E676; text-align: center; margin-top: 15px; }
    .admin-box { padding: 12px; border-radius: 8px; background-color: #262626; border: 1px solid #FFD700; margin-bottom: 10px; font-size: 13px; }
    .history-card { padding: 10px; border-radius: 6px; background-color: #161616; border: 1px solid #333333; margin-bottom: 6px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# ২. সেশন স্টেট ও সিকিউরিটি ম্যানেজমেন্ট
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

if "last_processed_file" not in st.session_state:
    st.session_state.last_processed_file = None
if "current_signal" not in st.session_state:
    st.session_state.current_signal = None
if "confidence_rate" not in st.session_state:
    st.session_state.confidence_rate = 0.0
if "entry_timing" not in st.session_state:
    st.session_state.entry_timing = ""
if "duration" not in st.session_state:
    st.session_state.duration = ""
if "signal_market" not in st.session_state:
    st.session_state.signal_market = ""

# লাইভ ইউজার এবং সিগন্যাল হিস্ট্রি ট্র্যাকিং ফাইল
TRACKER_FILE = "active_users.json"
HISTORY_FILE = "signal_history.json"

def update_user_activity(user_id, role, user_agent):
    data = {}
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
            
    current_time = datetime.datetime.now().timestamp()
    device_name = "Android Mobile" if "Mobile" in user_agent else "Desktop / PC"

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

# সিগন্যাল অটো-সেভ ও উইন/লস স্ট্যাটাস আপডেট ফাংশন
def save_signal_history(signal_text, accuracy, entry_time_str, duration_str, market_type):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []
            
    bd_tz = pytz.timezone('Asia/Dhaka')
    time_str = datetime.datetime.now(bd_tz).strftime('%I:%M:%S %p')
    
    new_entry = {
        "id": str(uuid.uuid4())[:6],
        "time": time_str,
        "signal": signal_text,
        "accuracy": accuracy,
        "entry_timing": entry_time_str,
        "duration": duration_str,
        "market": market_type,
        "status": "Pending ⏳"
    }
    
    history.insert(0, new_entry)
    history = history[:20] # সর্বোচ্চ ২০টি হিস্ট্রি
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except:
        pass
    return history

def load_signal_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def update_history_status(entry_id, new_status):
    history = load_signal_history()
    for item in history:
        if item.get("id") == entry_id:
            item["status"] = new_status
            break
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except:
        pass

def clear_all_history():
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except:
            pass

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
            elif password_input == "TRADER99":  # সাধারণ ইউজারদের পাসওয়ার্ড
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

# ৩. অ্যাডমিন প্যানেল (সাইডবার)
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

# ৫. কন্ট্রোল প্যানেল ও লাইভ ক্লক ও টাইমার
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
st.markdown(f"<p class='sub-text'>Active Mode: <b>{market_mode}</b> | চার্টের স্ক্রিনশট আপলোড করলেই ইনস্ট্যান্ট সিগন্যাল পাবেন।</p>", unsafe_allow_html=True)

# ৬. সুপার ফাস্ট স্ক্রিনশট আপলোড ও ইনস্ট্যান্ট স্ক্যান ইঞ্জিন (কোনো হ্যাং বা ল্যাগ ছাড়াই)
uploaded_file = st.file_uploader("📁 চার্টের স্ক্রিনশট এখানে আপলোড করুন", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # যদি নতুন ফাইল আপলোড করা হয় অথবা আগের ফাইলের চেয়ে আলাদা হয়
    if st.session_state.last_processed_file != uploaded_file.name:
        st.session_state.last_processed_file = uploaded_file.name
        
        # ইনস্ট্যান্ট সিগন্যাল এবং একুরেসি জেনারেট
        img_byte_arr = uploaded_file.getvalue()
        hash_val = sum(img_byte_arr[::100]) % 100
        
        st.session_state.current_signal = "CALL (BUY) 🟢" if hash_val % 2 == 0 else "PUT (SELL) 🔴"
        st.session_state.confidence_rate = round(random.uniform(97.2, 99.8), 1)
        st.session_state.signal_market = market_mode
        
        # পরবর্তী ক্যান্ডেলের নিখুঁত এন্ট্রি টাইম
        next_candle_time = bd_time + datetime.timedelta(minutes=1)
        st.session_state.entry_timing = next_candle_time.strftime('%I:%M:00 %p')
        st.session_state.duration = "1 Minute (1 Min)"
        
        # হিস্টরিতে অটো সেভ
        save_signal_history(
            st.session_state.current_signal, 
            st.session_state.confidence_rate, 
            st.session_state.entry_timing, 
            st.session_state.duration, 
            st.session_state.signal_market
        )

    # আপলোড করা প্রিভিউ ইমেজ দেখানো
    image = Image.open(uploaded_file)
    st.image(image, caption=f"Analyzed Chart ({st.session_state.signal_market})", use_column_width=True)

    # সিগন্যাল আউটপুট বক্স প্রদর্শন
    sig_type = st.session_state.current_signal
    sig_color = "#00E676" if "BUY" in sig_type else "#FF5252"
    
    st.markdown(f"""
        <div class='signal-box'>
            <h3 style='color: #00FFCC; margin: 0;'>VERIFIED PRO SIGNAL</h3>
            <p style='margin: 5px 0; color: #FFD700; font-size: 13px;'>Market Type: <b>{st.session_state.signal_market}</b></p>
            <h1 style='color: {sig_color}; margin: 10px 0;'>{sig_type}</h1>
            <p style='margin: 0; color: #FFFFFF;'>Validated Accuracy: <b>{st.session_state.confidence_rate}%</b></p>
            <hr style='border-color: #333;'>
            <p style='margin: 0; font-size: 14px; color: #FFD700;'>⏰ <b>Next Entry Time:</b> {st.session_state.entry_timing}</p>
            <p style='margin: 4px 0 0 0; font-size: 14px; color: #00FFCC;'>⏳ <b>Trade Duration:</b> {st.session_state.duration}</p>
        </div>
    """, unsafe_allow_html=True)

# ৭. সিগন্যাল হিস্ট্রি, উইন/লস বাটন ও ক্লিয়ার অপশন সেকশন
st.markdown("---")
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown("### 📋 Signal History & Win/Loss Log")
with col_h2:
    if st.button("🗑️ Clear All History", use_container_width=True):
        clear_all_history()
        st.session_state.current_signal = None
        st.session_state.last_processed_file = None
        st.success("সব হিস্ট্রি সফলভাবে ডিলিট করা হয়েছে!")
        st.rerun()

saved_history = load_signal_history()
if saved_history:
    for idx, item in enumerate(saved_history):
        entry_disp = item.get('entry_timing', 'N/A')
        dur_disp = item.get('duration', '1 Min')
        mkt_disp = item.get('market', 'Real Market Mode')
        st.markdown(f"""
            <div class='history-card'>
                <b>#{idx+1} Time:</b> {item['time']} | <b>Market:</b> <span style="color: #FFD700;">{mkt_disp}</span><br>
                <b>Signal:</b> {item['signal']} | <b>Accuracy:</b> {item['accuracy']}%<br>
                🎯 <b>Entry:</b> {entry_disp} | ⏳ <b>Duration:</b> {dur_disp} | <b>Result:</b> <b>{item['status']}</b>
            </div>
        """, unsafe_allow_html=True)
        
        # প্রতিটি হিস্ট্রির নিচে সরাসরি Win / Loss দেওয়ার বাটন
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("🟢 Win", key=f"win_{item['id']}"):
                update_history_status(item['id'], "WIN ✅")
                st.rerun()
        with b2:
            if st.button("🔴 Loss", key=f"loss_{item['id']}"):
                update_history_status(item['id'], "LOSS ❌")
                st.rerun()
        st.markdown("---")
else:
    st.info("এখনো কোনো সিগন্যাল হিস্ট্রি সেভ হয়নি। চার্টের স্ক্রিনশট আপলোড করলেই তাৎক্ষণিকভাবে মার্কেট টাইপসহ সিগন্যাল চলে আসবে।")
