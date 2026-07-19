from html import escape as html_escape

import streamlit as st
from backend.database.db import Database
from frontend.utils.ingest import ingest_documents


def _inject_auth_css():
    st.markdown("""
<style>
    .auth-container {
        min-height: 100vh; display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        background: #0F172A; position: relative; overflow: hidden;
        padding: 24px;
    }
    .auth-bg-glow {
        position: fixed; inset: 0; pointer-events: none; z-index: 0;
    }
    .auth-bg-glow::before {
        content: ''; position: absolute;
        top: -10%; left: -10%; width: 40%; height: 40%;
        background: rgba(192,193,255,0.08); border-radius: 50%;
        filter: blur(120px);
    }
    .auth-bg-glow::after {
        content: ''; position: absolute;
        bottom: -10%; right: -10%; width: 40%; height: 40%;
        background: rgba(208,188,255,0.08); border-radius: 50%;
        filter: blur(120px);
    }
    .auth-header { text-align: center; margin-bottom: 32px; position: relative; z-index: 1; }
    .auth-header .voice-bars {
        display: flex; align-items: flex-end; justify-content: center;
        gap: 4px; height: 32px; margin-bottom: 16px;
    }
    .auth-header .voice-bars div {
        width: 6px; border-radius: 3px; background: #c0c1ff;
        animation: voice-pulse 1.5s ease-in-out infinite;
    }
    .auth-header .voice-bars div:nth-child(1) { height: 12px; animation-delay: 0.1s; }
    .auth-header .voice-bars div:nth-child(2) { height: 24px; animation-delay: 0.3s; }
    .auth-header .voice-bars div:nth-child(3) { height: 8px; animation-delay: 0.2s; background: #8083ff; }
    .auth-header .voice-bars div:nth-child(4) { height: 20px; animation-delay: 0.4s; background: #d0bcff; }
    .auth-header .voice-bars div:nth-child(5) { height: 14px; animation-delay: 0.15s; }
    @keyframes voice-pulse {
        0%, 100% { transform: scaleY(0.5); } 50% { transform: scaleY(1.2); }
    }
    .auth-header h1 {
        font-size: 32px; font-weight: 700; line-height: 1.2;
        background: linear-gradient(135deg, #c0c1ff, #d0bcff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .auth-header p { color: #c7c4d7; font-size: 16px; margin-top: 8px; }
    .auth-card {
        background: rgba(30,41,59,0.8); backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px; padding: 32px; width: 100%; max-width: 520px;
        position: relative; z-index: 1;
        box-shadow: 0 0 60px rgba(99,102,241,0.1);
    }
    .auth-footer {
        margin-top: 24px; display: flex; justify-content: space-between;
        align-items: center; padding: 0 16px;
        color: #464554; font-size: 12px; position: relative; z-index: 1;
        width: 100%; max-width: 520px;
    }
    .auth-footer a { color: #908fa0; text-decoration: none; }
    .auth-footer a:hover { color: #c7c4d7; }
</style>
""", unsafe_allow_html=True)


def _ingest_documents(user_id: str, cv_file, jd_file):
    vs = ingest_documents(user_id, cv_file, jd_file)
    st.session_state.db = Database()
    return vs


def render_auth():
    _inject_auth_css()

    st.markdown('<div class="auth-container"><div class="auth-bg-glow"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-header">
        <div class="voice-bars">
            <div></div><div></div><div></div><div></div><div></div>
        </div>
        <h1>AI Mock Interviewer</h1>
        <p>Upload your resume and job description to start practicing.</p>
    </div>
    <div class="auth-card">
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "New User"])

    with tab1:
        with st.form("login_form", border=False):
            st.markdown('<div style="margin-bottom: 16px">', unsafe_allow_html=True)
            user_id = st.text_input("User ID", placeholder="Enter your unique ID", key="login_id")
            col_cv, col_jd = st.columns(2)
            with col_cv:
                cv_file = st.file_uploader("CV (optional)", type=["pdf", "docx", "txt"], key="login_cv")
            with col_jd:
                jd_file = st.file_uploader("JD (optional)", type=["pdf", "docx", "txt"], key="login_jd")
            st.markdown('</div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("Start Interview", use_container_width=True, type="primary")
            if submitted and user_id.strip():
                from backend.security import validate_user_id
                try:
                    validate_user_id(user_id.strip())
                except Exception:
                    st.error("Invalid User ID. Use only letters, numbers, dash, or underscore (1-64 chars).")
                    st.stop()
                if cv_file and jd_file:
                    _ingest_documents(user_id.strip(), cv_file, jd_file)
                from frontend.utils.session import login
                login(user_id.strip())
                st.rerun()

    with tab2:
        with st.form("register_form", border=False):
            user_id = st.text_input("Create User ID", placeholder="e.g. user_8892", key="register_id")
            st.caption("Save this ID to resume your session later.")
            col_cv, col_jd = st.columns(2)
            with col_cv:
                cv_file = st.file_uploader("CV (required)", type=["pdf", "docx", "txt"], key="register_cv")
            with col_jd:
                jd_file = st.file_uploader("JD (required)", type=["pdf", "docx", "txt"], key="register_jd")
            submitted = st.form_submit_button("Register & Start", use_container_width=True, type="primary")
            if submitted and user_id.strip() and cv_file and jd_file:
                from backend.security import validate_user_id
                try:
                    validate_user_id(user_id.strip())
                except Exception:
                    st.error("Invalid User ID. Use only letters, numbers, dash, or underscore (1-64 chars).")
                    st.stop()
                _ingest_documents(user_id.strip(), cv_file, jd_file)
                from frontend.utils.session import login
                login(user_id.strip())
                st.rerun()

    st.markdown("""
    </div>
    <div class="auth-footer">
        <div><span>✓</span> Secure AI Protocol</div>
        <div><a href="#">Support</a> &middot; <a href="#">Privacy</a></div>
    </div>
    </div>
    """, unsafe_allow_html=True)
