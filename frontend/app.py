import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
    if not os.getenv("GROQ_API_KEY"):
        load_dotenv()
else:
    load_dotenv()

_key = os.getenv("GROQ_API_KEY", "")
if not _key:
    print("=" * 60, file=sys.stderr)
    print("ERROR: GROQ_API_KEY is not set!", file=sys.stderr)
    print("Create a .env file in the project root with:", file=sys.stderr)
    print("  GROQ_API_KEY=gsk_your_key_here", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

import streamlit as st

st.set_page_config(
    page_title="AI Mock Interviewer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from html import escape as html_escape

from frontend.utils.session import init_session_state
from frontend.pages.auth import render_auth
from frontend.pages.interview import render_interview
from frontend.pages.dashboard import render_dashboard


def inject_css():
    st.markdown("""
<style>
    .stApp, .stApp > header { background: #0F172A !important; }
    .stApp > header { border-bottom: 1px solid rgba(255,255,255,0.05); }
    #MainMenu, .stDeployButton, footer { display: none !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #464554; border-radius: 10px; }
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .glass-card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 0 40px rgba(99,102,241,0.08);
    }

    section[data-testid="stSidebar"] { display: none; }

    div.stButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
        border: none !important; transition: all 0.2s !important;
        height: 44px !important; font-size: 14px !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
        color: #fff !important; box-shadow: 0 0 20px rgba(99,102,241,0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 0 30px rgba(99,102,241,0.5) !important;
    }
    div.stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.05) !important;
        color: #e0e3e5 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    div.stTextInput > div > div > input,
    div.stTextArea > div > div >textarea {
        background: #1e293b !important; border: 2px solid transparent !important;
        border-radius: 12px !important; color: #e0e3e5 !important;
        font-size: 14px !important; padding: 12px 16px !important;
    }
    div.stTextInput > div > div > input:focus,
    div.stTextArea > div > div >textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.1) !important;
    }

    div.stFileUploader > section {
        border: 2px dashed rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        background: rgba(255,255,255,0.02) !important;
        padding: 16px !important;
    }
    div.stFileUploader > section:hover {
        border-color: #6366F1 !important;
        background: rgba(99,102,241,0.05) !important;
    }
    div.stFileUploader > section > button {
        background: rgba(99,102,241,0.15) !important;
        color: #c0c1ff !important; border-radius: 8px !important;
    }

    div.stMetric {
        background: #1e293b; border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px; padding: 12px 16px;
    }
    div.stMetric label {
        color: #c7c4d7 !important; font-size: 12px !important;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    div.stMetric div[data-testid="stMetricValue"] {
        color: #e0e3e5 !important; font-size: 24px !important;
        font-weight: 700 !important;
    }

    div.stTabs > div > button {
        border-radius: 10px !important; padding: 8px 24px !important;
        font-weight: 600 !important; font-size: 14px !important;
    }
    div.stTabs > div > button[aria-selected="true"] {
        background: rgba(87,27,193,0.3) !important;
        color: #c4abff !important;
        box-shadow: 0 0 20px rgba(87,27,193,0.2) !important;
    }

    div[data-testid="stChatMessageContent"] {
        border-radius: 16px !important; padding: 12px 16px !important;
        font-size: 14px !important; line-height: 1.6 !important;
    }
    .chat-ai div[data-testid="stChatMessageContent"] {
        background: #1e293b !important; color: #e0e3e5 !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
    }
    .chat-user div[data-testid="stChatMessageContent"] {
        background: rgba(87,27,193,0.3) !important; color: #e0e3e5 !important;
    }
    .chat-feedback div[data-testid="stChatMessageContent"] {
        background: rgba(99,102,241,0.08) !important;
        border-left: 3px solid #6366F1 !important;
        border-radius: 8px !important; font-size: 13px !important;
    }

    div.stAlert { border-radius: 12px !important; border: none !important; }
    .stSuccess { background: rgba(34,197,94,0.1) !important; color: #22C55E !important; }
    .stWarning { background: rgba(245,158,11,0.1) !important; color: #F59E0B !important; }
    .stError { background: rgba(239,68,68,0.1) !important; color: #ffb4ab !important; }
    .stInfo { background: rgba(59,130,246,0.1) !important; color: #60a5fa !important; }

    div.streamlit-expanderHeader {
        background: transparent !important; border-radius: 12px !important;
        font-weight: 600 !important; color: #e0e3e5 !important;
    }
    div.streamlit-expanderContent {
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 0 0 12px 12px !important;
        background: rgba(30,41,59,0.5) !important;
    }

    hr { border-color: rgba(255,255,255,0.06) !important; margin: 16px 0 !important; }
    div[data-testid="column"] { gap: 16px !important; }
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
    }
</style>
""", unsafe_allow_html=True)


init_session_state()

if not st.session_state.logged_in:
    render_auth()
else:
    inject_css()

    page = st.session_state.get("page", "interview")
    user_initial = html_escape(st.session_state.user_id[0].upper()) if st.session_state.user_id else "U"
    safe_user_id = html_escape(st.session_state.user_id)

    st.markdown(f"""
    <style>
    .top-nav {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 32px; height: 64px;
        background: rgba(15,23,42,0.85);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    }}
    .top-nav .logo {{
        font-size: 22px; font-weight: 700;
        background: linear-gradient(135deg, #c0c1ff, #d0bcff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .top-nav .nav-links {{ display: flex; gap: 8px; }}
    .top-nav .nav-links a {{
        padding: 8px 20px; border-radius: 10px; font-size: 14px;
        font-weight: 500; cursor: pointer; color: #c7c4d7;
        text-decoration: none; transition: all 0.2s;
    }}
    .top-nav .nav-links a:hover {{ color: #e0e3e5; background: rgba(255,255,255,0.05); }}
    .top-nav .nav-links a.active {{
        color: #c0c1ff; background: rgba(192,193,255,0.1);
    }}
    .top-nav .user-section {{ display: flex; align-items: center; gap: 12px; }}
    .top-nav .user-avatar {{
        width: 36px; height: 36px; border-radius: 50%;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; font-weight: 600; color: #fff;
        border: 2px solid rgba(192,193,255,0.3);
    }}
    .top-nav .user-name {{ font-size: 14px; color: #e0e3e5; font-weight: 500; }}
    </style>
    <div class="top-nav">
        <div class="logo">AI Mock Interviewer</div>
        <div></div>
        <div class="user-section">
            <div class="user-avatar">{user_initial}</div>
            <span class="user-name">{safe_user_id}</span>
        </div>
    </div>
    <div style="height:80px"></div>
    """, unsafe_allow_html=True)

    nav_cols = st.columns([1, 1, 6])
    with nav_cols[0]:
        if st.button("🎤 Interview", use_container_width=True,
                     type="primary" if page == "interview" else "secondary"):
            st.session_state.page = "interview"
            st.rerun()
    with nav_cols[1]:
        if st.button("📊 Dashboard", use_container_width=True,
                     type="primary" if page == "dashboard" else "secondary"):
            st.session_state.page = "dashboard"
            st.rerun()
    with nav_cols[2]:
        if st.button("Logout", use_container_width=True, type="secondary"):
            from frontend.utils.session import logout
            logout()
            st.rerun()

    if st.session_state.page == "interview":
        render_interview()
    elif st.session_state.page == "dashboard":
        render_dashboard()
