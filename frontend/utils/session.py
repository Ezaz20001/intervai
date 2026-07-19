import streamlit as st
from typing import Optional

from backend.security import (
    create_session_token,
    validate_session_token,
    validate_user_id,
    cleanup_expired_tokens,
)


def init_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "auth"
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "db" not in st.session_state:
        st.session_state.db = None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "llm" not in st.session_state:
        st.session_state.llm = None
    if "feedback_engine" not in st.session_state:
        st.session_state.feedback_engine = None
    if "analytics" not in st.session_state:
        st.session_state.analytics = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None


def login(user_id: str):
    validate_user_id(user_id)
    token = create_session_token(user_id)
    st.session_state.user_id = user_id
    st.session_state.logged_in = True
    st.session_state.session_token = token
    st.session_state.page = "interview"


def logout():
    cleanup_expired_tokens()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


def navigate(page: str):
    st.session_state.page = page
