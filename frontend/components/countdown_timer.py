import time
import streamlit as st

from backend import config


def render_countdown_timer(key_prefix: str = "main") -> dict:
    timer_key = f"{key_prefix}_timer_start"
    duration_key = f"{key_prefix}_timer_duration"
    active_key = f"{key_prefix}_timer_active"

    if timer_key not in st.session_state:
        st.session_state[timer_key] = None
    if duration_key not in st.session_state:
        st.session_state[duration_key] = config.COUNTDOWN_SECONDS
    if active_key not in st.session_state:
        st.session_state[active_key] = False

    result = {"expired": False, "remaining": 0, "elapsed": 0}

    if not st.session_state[active_key]:
        if st.button("Start Timer", key=f"{key_prefix}_start_timer",
                     use_container_width=True, type="secondary"):
            st.session_state[timer_key] = time.time()
            st.session_state[active_key] = True
            st.rerun()
        result["remaining"] = st.session_state[duration_key]
        return result

    if st.session_state[timer_key] is None:
        st.session_state[timer_key] = time.time()

    elapsed = time.time() - st.session_state[timer_key]
    remaining = max(0, st.session_state[duration_key] - elapsed)
    result["remaining"] = int(remaining)
    result["elapsed"] = int(elapsed)

    if remaining <= 0:
        result["expired"] = True
        st.session_state[active_key] = False
        st.session_state[timer_key] = None

    minutes = int(remaining) // 60
    seconds = int(remaining) % 60
    pct = remaining / st.session_state[duration_key] * 100

    if remaining <= 30:
        color = "#ef4444"
        pulse = "timer-pulse"
    elif remaining <= 60:
        color = "#F59E0B"
        pulse = ""
    else:
        color = "#6366F1"
        pulse = ""

    st.markdown(f"""
    <style>
    @keyframes timer-pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.6; }}
    }}
    .timer-display {{
        background: rgba(30,41,59,0.75);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
    }}
    .timer-display .time {{
        font-size: 32px;
        font-weight: 700;
        color: {color};
        font-family: 'JetBrains Mono', monospace;
        {'animation: timer-pulse 1s ease-in-out infinite;' if pulse else ''}
    }}
    .timer-display .label {{
        font-size: 11px;
        color: #c7c4d7;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }}
    .timer-bar {{
        height: 4px;
        background: #1e293b;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 8px;
    }}
    .timer-bar .fill {{
        height: 100%;
        background: {color};
        border-radius: 2px;
        transition: width 1s linear;
        width: {pct}%;
    }}
    </style>
    <div class="timer-display">
        <div class="time">{minutes:02d}:{seconds:02d}</div>
        <div class="label">Time Remaining</div>
        <div class="timer-bar"><div class="fill"></div></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Reset Timer", key=f"{key_prefix}_reset_timer",
                 use_container_width=True, type="secondary"):
        st.session_state[timer_key] = time.time()
        st.session_state[active_key] = True
        st.rerun()

    return result
