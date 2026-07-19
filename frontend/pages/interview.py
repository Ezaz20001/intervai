import time
from html import escape as html_escape

import streamlit as st
import numpy as np
from PIL import Image

from backend.llm.service import LLMService
from backend.orchestrator.interviewer import InterviewOrchestrator
from backend.feedback.engine import FeedbackEngine
from backend.analytics.service import AnalyticsService
from backend.database.db import Database
from backend.vector_store.store import VectorStore
from backend.voice.tts import text_to_speech
from backend.voice.stt import transcribe_audio_data
from backend.vision.analyzer import VisionAnalyzer
from backend.emotion.analyzer import analyze_text
from backend import config
from frontend.utils.ingest import ingest_documents
from frontend.components.radar_chart import create_session_radar
from frontend.components.countdown_timer import render_countdown_timer


def _speak(text: str):
    audio_bytes = text_to_speech(text)
    st.session_state._last_audio = audio_bytes


def _has_documents() -> bool:
    vs = st.session_state.get("vector_store")
    if vs is None:
        return False
    user_id = st.session_state.get("user_id", "")
    if not user_id:
        return False
    try:
        result = vs.similarity_search("", n_results=1, filter_metadata={"user_id": user_id})
        return len(result) > 0
    except Exception:
        return False


def _init_services():
    if st.session_state.llm is None:
        st.session_state.llm = LLMService()
    if st.session_state.feedback_engine is None:
        st.session_state.feedback_engine = FeedbackEngine()
    if st.session_state.db is None:
        st.session_state.db = Database()
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore()
    if st.session_state.analytics is None:
        st.session_state.analytics = AnalyticsService(
            st.session_state.db, st.session_state.vector_store
        )
    if st.session_state.get("vision") is None:
        st.session_state.vision = VisionAnalyzer()
    if "emotion_history" not in st.session_state:
        st.session_state.emotion_history = []


def render_interview():
    _init_services()

    st.markdown("""
<style>
    .cam-wrap { border-radius:16px; overflow:hidden; border:1px solid rgba(255,255,255,0.08); position:relative; }
    .cam-wrap .badge {
        position:absolute; top:8px; left:12px; z-index:10;
        display:flex; align-items:center; gap:6px;
        background:rgba(0,0,0,0.5); backdrop-filter:blur(4px);
        padding:4px 10px; border-radius:20px;
    }
    .cam-wrap .badge .dot { width:8px; height:8px; border-radius:50%; background:#ef4444; animation:pulse-cam 1.5s infinite; }
    .cam-wrap .badge span { color:#e0e3e5; font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; }
    @keyframes pulse-cam { 0%,100%{opacity:1} 50%{opacity:0.5} }
    .cam-wrap > div[data-testid="stCameraInput"] > div { border:none !important; border-radius:0 !important; }

    .ctrl-card {
        background:rgba(30,41,59,0.75); backdrop-filter:blur(16px);
        border:1px solid rgba(255,255,255,0.08); border-radius:16px;
        padding:16px; box-shadow:0 0 40px rgba(99,102,241,0.08);
    }
    .ctrl-progress { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
    .ctrl-progress span:first-child { color:#c7c4d7; font-size:12px; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; }
    .ctrl-progress span:last-child { color:#c0c1ff; font-size:12px; font-weight:600; }
    .ctrl-bar { height:6px; background:#1e293b; border-radius:3px; overflow:hidden; margin-bottom:16px; }
    .ctrl-bar .fill { height:100%; background:linear-gradient(90deg,#6366F1,#8B5CF6); border-radius:3px; box-shadow:0 0 10px rgba(99,102,241,0.4); transition:width 0.5s; }

    .docs-card {
        background:rgba(30,41,59,0.75); backdrop-filter:blur(16px);
        border:1px solid rgba(255,255,255,0.08); border-radius:16px;
        padding:16px; box-shadow:0 0 40px rgba(99,102,241,0.08);
    }

    .chat-card {
        background:rgba(30,41,59,0.75); backdrop-filter:blur(16px);
        border:1px solid rgba(255,255,255,0.08); border-radius:16px;
        overflow:hidden; box-shadow:0 0 40px rgba(99,102,241,0.08);
        display:flex; flex-direction:column; min-height:600px;
    }
    .chat-msgs { padding:20px; flex-grow:1; overflow-y:auto; max-height:480px; }
    .msg-row { display:flex; align-items:flex-start; gap:8px; margin-bottom:12px; }
    .msg-row.user { flex-direction:row-reverse; }
    .msg-av {
        width:28px; height:28px; border-radius:50%; flex-shrink:0;
        display:flex; align-items:center; justify-content:center; font-size:13px;
    }
    .msg-av.ai { background:rgba(192,193,255,0.15); color:#c0c1ff; }
    .msg-av.user { background:rgba(208,188,255,0.15); color:#d0bcff; }
    .msg-bub {
        max-width:80%; padding:12px 16px; border-radius:16px;
        font-size:14px; line-height:1.6;
    }
    .msg-bub.ai { background:#1e293b; color:#e0e3e5; border:1px solid rgba(255,255,255,0.05); border-top-left-radius:4px; }
    .msg-bub.user { background:rgba(87,27,193,0.3); color:#e0e3e5; border-top-right-radius:4px; }
    .msg-bub.fb {
        background:rgba(99,102,241,0.08); color:#c7c4d7;
        border-left:3px solid #6366F1; border-radius:8px;
        font-size:13px; margin:8px 0 8px 36px;
    }
    .chat-input {
        padding:16px 20px; border-top:1px solid rgba(255,255,255,0.05);
    }

    .analytics-card {
        background:rgba(30,41,59,0.75); backdrop-filter:blur(16px);
        border:1px solid rgba(255,255,255,0.08); border-radius:16px;
        padding:16px; box-shadow:0 0 40px rgba(99,102,241,0.08);
        margin-bottom:16px;
    }
    .roadmap-card {
        background:rgba(30,41,59,0.75); backdrop-filter:blur(16px);
        border:1px solid rgba(255,255,255,0.08); border-radius:16px;
        padding:16px; box-shadow:0 0 40px rgba(99,102,241,0.08);
    }
    .road-item { display:flex; align-items:center; gap:12px; padding:8px 0; }

    .cited-card {
        background:rgba(99,102,241,0.05); border:1px solid rgba(99,102,241,0.15);
        border-radius:10px; padding:10px 12px; margin:6px 0;
    }
    .cited-card .cited-label { font-size:10px; color:#c0c1ff; text-transform:uppercase; letter-spacing:0.05em; font-weight:600; margin-bottom:4px; }
    .cited-card .cited-text { font-size:12px; color:#c7c4d7; line-height:1.5; }
</style>
""", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "_q_count" not in st.session_state:
        st.session_state._q_count = 0
    if "_last_audio" not in st.session_state:
        st.session_state._last_audio = None

    left_col, center_col, right_col = st.columns([3, 5, 3])

    # ═══════════════════════════════════════════
    # LEFT COLUMN
    # ═══════════════════════════════════════════
    with left_col:
        vision = st.session_state.vision
        camera_disabled = not st.session_state.interview_active
        camera_image = st.camera_input(
            "Webcam Feed",
            key="webcam",
            disabled=camera_disabled,
            label_visibility="collapsed",
        )
        if camera_image is not None:
            img = Image.open(camera_image)
            frame = np.array(img)
            frame_bgr = frame[:, :, ::-1]
            analysis = vision.analyze_frame(frame_bgr)
            st.session_state._last_vision = analysis
            overlay = vision.draw_overlay(frame_bgr.copy(), analysis)
            overlay_rgb = overlay[:, :, ::-1]
            st.image(overlay_rgb, use_container_width=True)

            if "vision_history" not in st.session_state:
                st.session_state.vision_history = []
            st.session_state.vision_history.append({
                "time": time.time(),
                "eye_contact": analysis["eye_contact"],
                "head_pose": analysis["head_pose"],
            })

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        q_count = st.session_state.get("_q_count", 0)
        progress_pct = min(q_count / max(config.SESSION_QUESTION_LIMIT, 1), 1.0) * 100
        st.markdown(f"""
        <div class="ctrl-card">
            <div class="ctrl-progress">
                <span>Progress</span>
                <span>{q_count}/{config.SESSION_QUESTION_LIMIT}</span>
            </div>
            <div class="ctrl-bar">
                <div class="fill" style="width:{progress_pct}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.interview_active:
            st.markdown("**Interview Timer**")
            timer_result = render_countdown_timer("interview")
            if timer_result.get("expired"):
                st.warning("Time is up! Please submit your current answer.")
                st.session_state.messages.append({
                    "role": "system",
                    "content": "Time expired for this question."
                })

        if not st.session_state.interview_active:
            if st.button("Start Interview", type="primary", use_container_width=True):
                orch = InterviewOrchestrator(
                    llm=st.session_state.llm,
                    vector_store=st.session_state.vector_store,
                    db=st.session_state.db,
                    feedback_engine=st.session_state.feedback_engine,
                )
                orch.start_session(st.session_state.user_id, "")
                st.session_state.orchestrator = orch
                st.session_state.interview_active = True
                st.session_state.messages = []
                st.session_state.emotion_history = []
                st.session_state.vision_history = []
                st.session_state._q_count = 0
                st.session_state["interview_timer_start"] = time.time()
                st.session_state["interview_timer_active"] = True

                with st.spinner("Generating first question..."):
                    question = orch.next_question()
                    st.session_state.current_question = question
                    st.session_state.messages.append({"role": "assistant", "content": question})
                    if orch.cited_entries:
                        st.session_state._last_cited = orch.cited_entries
                    _speak(question)
                st.rerun()
        else:
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("End Session", type="primary", use_container_width=True):
                    st.session_state.orchestrator.end_session()
                    st.session_state.interview_active = False
                    st.rerun()
            with bcol2:
                if st.button("Skip", type="secondary", use_container_width=True):
                    with st.spinner("Next question..."):
                        nq = st.session_state.orchestrator.next_question()
                        st.session_state.current_question = nq
                        st.session_state._q_count += 1
                        st.session_state.messages.append({"role": "assistant", "content": nq})
                        if st.session_state.orchestrator.cited_entries:
                            st.session_state._last_cited = st.session_state.orchestrator.cited_entries
                    st.rerun()

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        has_docs = _has_documents()
        st.markdown(f"""
        <div class="ctrl-card">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span style="font-size:18px">📁</span>
                <span style="color:#e0e3e5;font-size:14px;font-weight:600">Resume &amp; JD</span>
                <span style="margin-left:auto;color:{'#22C55E' if has_docs else '#F59E0B'};font-size:12px">
                    {'✅ Loaded' if has_docs else '⚠️ Not uploaded'}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Upload / Update Documents", expanded=not has_docs):
            cv_file = st.file_uploader("CV (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="int_cv")
            jd_file = st.file_uploader("Job Description", type=["pdf", "docx", "txt"], key="int_jd")
            if cv_file and jd_file:
                if st.button("Upload & Ingest", type="primary", use_container_width=True):
                    ingest_documents(st.session_state.user_id, cv_file, jd_file)
                    st.success("Documents ingested!")
                    st.rerun()

    # ═══════════════════════════════════════════
    # CENTER COLUMN
    # ═══════════════════════════════════════════
    with center_col:
        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        st.markdown('<div class="chat-msgs">', unsafe_allow_html=True)
        msgs = st.session_state.get("messages", [])
        if not msgs and not st.session_state.interview_active:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:60px 20px;text-align:center">
                <div style="font-size:48px;margin-bottom:16px;opacity:0.6">🎙️</div>
                <h3 style="color:#c7c4d7;font-size:18px;font-weight:600;margin:0 0 8px">Ready for Your Interview?</h3>
                <p style="color:#464554;font-size:14px;max-width:320px;line-height:1.6">
                    Upload your resume and job description, then click <strong style="color:#c0c1ff">Start Interview</strong> to begin.
                </p>
            </div>
            """, unsafe_allow_html=True)
        for msg in msgs:
            if msg["role"] == "assistant":
                is_fb = "Score:" in msg["content"]
                with st.chat_message("assistant", avatar="🤖" if not is_fb else "💡"):
                    st.markdown(msg["content"])
            elif msg["role"] == "system":
                with st.chat_message("assistant", avatar="⏰"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])

        last_audio = st.session_state.get("_last_audio")
        if last_audio is not None:
            st.audio(last_audio, autoplay=True)
            st.session_state._last_audio = None
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.interview_active:
            st.markdown('<div class="chat-input">', unsafe_allow_html=True)

            audio_data = st.audio_input(
                "Record your answer",
                key=f"audio_{st.session_state._q_count}",
                label_visibility="collapsed",
            )
            if audio_data is not None:
                with st.status("Transcribing...", expanded=True) as status:
                    audio_bytes = audio_data.getvalue()
                    status.write("Processing audio...")
                    answer = transcribe_audio_data(audio_bytes)
                    if not answer:
                        st.warning("Transcription failed. Type your answer below.")
                        answer = st.text_input("Your answer:", key=f"fallback_{st.session_state._q_count}")
                        if not st.button("Submit", key=f"fb_{st.session_state._q_count}"):
                            st.stop()

                    status.write(f"**{answer}**")
                    emotion = analyze_text(answer)
                    st.session_state.emotion_history.append(emotion)
                    status.write(f"Confidence: {emotion['confidence_score']}/10")
                    status.update(label="Evaluating...", state="running")

                    result = st.session_state.orchestrator.submit_answer(answer)
                    st.session_state._q_count += 1
                    score = result.get("score", 0)
                    topic = result.get("topic", "general")
                    feedback = (
                        f"**Score: {score}/10** | Topic: *{topic}*\n\n"
                        f"**Strengths**\n{result.get('strengths', '')}\n\n"
                        f"**Areas to Improve**\n{result.get('improvements', '')}\n\n"
                        f"**Suggested Answer**\n{result.get('better_phrasing', '')}"
                    )
                    if result.get("star_score"):
                        feedback += f"\n\n---\n**STAR:** {result['star_score']}/10 | **Coherence:** {result.get('coherence_score', '-')}/10 | **Keywords:** {result.get('keyword_score', '-')}/10"
                    if result.get("matched_keywords"):
                        feedback += f"\n\n**Matched Keywords:** {', '.join(result['matched_keywords'][:5])}"
                    if result.get("missing_keywords"):
                        feedback += f"\n\n**Missing Keywords:** {', '.join(result['missing_keywords'][:3])}"

                    st.session_state.messages.append({"role": "user", "content": answer})
                    st.session_state.messages.append({"role": "assistant", "content": feedback})
                    st.session_state._last_grading = result
                    status.update(label="Complete!", state="complete")
                st.rerun()

            with st.form(key=f"tf_{st.session_state._q_count}", clear_on_submit=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    ta = st.text_input(
                        "Answer",
                        label_visibility="collapsed",
                        placeholder="Type your response or click the mic to speak...",
                    )
                with cols[1]:
                    sub = st.form_submit_button("Send", use_container_width=True)
                if sub and ta:
                    emotion = analyze_text(ta)
                    st.session_state.emotion_history.append(emotion)
                    result = st.session_state.orchestrator.submit_answer(ta)
                    st.session_state._q_count += 1
                    score = result.get("score", 0)
                    topic = result.get("topic", "general")
                    fb = (
                        f"**Score: {score}/10** | Topic: *{topic}*\n\n"
                        f"**Strengths**\n{result.get('strengths', '')}\n\n"
                        f"**Areas to Improve**\n{result.get('improvements', '')}\n\n"
                        f"**Suggested Answer**\n{result.get('better_phrasing', '')}"
                    )
                    if result.get("star_score"):
                        fb += f"\n\n---\n**STAR:** {result['star_score']}/10 | **Coherence:** {result.get('coherence_score', '-')}/10 | **Keywords:** {result.get('keyword_score', '-')}/10"
                    if result.get("matched_keywords"):
                        fb += f"\n\n**Matched Keywords:** {', '.join(result['matched_keywords'][:5])}"

                    st.session_state.messages.append({"role": "user", "content": ta})
                    st.session_state.messages.append({"role": "assistant", "content": fb})
                    st.session_state._last_grading = result
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        msgs = st.session_state.get("messages", [])
        if msgs and msgs[-1]["role"] == "assistant":
            has_fb = "Score:" in msgs[-1]["content"]
            if has_fb and st.session_state.interview_active:
                orch = st.session_state.orchestrator
                if orch.is_active:
                    with st.spinner("Next question..."):
                        nq = orch.next_question()
                        st.session_state.current_question = nq
                        st.session_state.messages.append({"role": "assistant", "content": nq})
                        if orch.cited_entries:
                            st.session_state._last_cited = orch.cited_entries
                        _speak(nq)
                    st.rerun()
                else:
                    orch.end_session()
                    st.session_state.interview_active = False
                    st.success("Session complete! View your results on the dashboard.")

    # ═══════════════════════════════════════════
    # RIGHT COLUMN
    # ═══════════════════════════════════════════
    with right_col:
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <span style="color:#c0c1ff">📊</span>
            <h3 style="color:#e0e3e5;font-size:14px;font-weight:600;margin:0">Live Performance</h3>
        </div>
        """, unsafe_allow_html=True)

        emotion = st.session_state.emotion_history[-1] if st.session_state.emotion_history else None
        no_data = emotion is None and not st.session_state.interview_active
        if no_data:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;padding:24px 8px;text-align:center">
                <span style="font-size:32px;opacity:0.5">📈</span>
                <p style="color:#464554;font-size:13px;margin:8px 0 0;line-height:1.5">
                    Start an interview session to see live performance metrics here.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            mc1, mc2 = st.columns(2)
            with mc1:
                st.metric("Score", f"{emotion['confidence_score']}/10" if emotion else "—")
            with mc2:
                st.metric("Confidence", f"{emotion['confidence_score']}/10" if emotion else "—")
            mc3, mc4 = st.columns(2)
            with mc3:
                st.metric("Fillers", str(emotion.get("filler_count", 0)) if emotion else "0")
            with mc4:
                st.metric("Questions", str(st.session_state.get("_q_count", 0)))

        if emotion:
            sent = emotion.get("sentiment", {})
            pos = sent.get("pos", 0)
            neu = sent.get("neu", 0)
            neg = sent.get("neg", 0)
            st.markdown("**Sentiment**")
            cols = st.columns(3)
            with cols[0]:
                st.metric("Positive", f"{pos:.0%}")
            with cols[1]:
                st.metric("Neutral", f"{neu:.0%}")
            with cols[2]:
                st.metric("Negative", f"{neg:.0%}")

        vision_data = st.session_state.get("_last_vision")
        if vision_data:
            eye_pct = 92 if vision_data["eye_contact"] else 30
            st.markdown("**Vision Metrics**")
            st.progress(eye_pct / 100, text=f"Eye Contact: {eye_pct}%")
            st.progress(78 / 100, text="Head Pose: 78%")
        st.markdown('</div>', unsafe_allow_html=True)

        last_grading = st.session_state.get("_last_grading")
        if last_grading and last_grading.get("star_score"):
            st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
            st.markdown("**Answer Quality Radar**")
            radar_data = {
                "star_score": last_grading.get("star_score", 0),
                "coherence_score": last_grading.get("coherence_score", 0),
                "keyword_score": last_grading.get("keyword_score", 0),
            }
            fig = create_session_radar(radar_data)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        last_cited = st.session_state.get("_last_cited", [])
        if last_cited:
            st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
            st.markdown("**Cited Resume Entries**")
            for entry in last_cited:
                st.markdown(f"""
                <div class="cited-card">
                    <div class="cited-label">{entry.get('source', 'cv').upper()}</div>
                    <div class="cited-text">{html_escape(entry.get('text', ''))}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("**Session Roadmap**")

        roadmap_topics = [
            ("Introduction", True),
            ("Experience Review", True),
            ("Technical Depth", False),
            ("System Design", False),
        ]
        for topic, done in roadmap_topics:
            is_cur = topic == "Technical Depth"
            status_icon = "✓" if done else ("●" if is_cur else "○")
            st.markdown(f"{status_icon} {topic}")
