from html import escape as html_escape

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from backend.database.db import Database
from backend.vector_store.store import VectorStore
from backend.analytics.service import AnalyticsService
from backend.evaluation.drift_monitor import DriftMonitor
from backend.reports.pdf_report import ReportGenerator
from backend import config
from frontend.components.radar_chart import create_radar_chart


def _get_analytics():
    if st.session_state.analytics is None:
        db = Database()
        vs = VectorStore()
        st.session_state.analytics = AnalyticsService(db, vs)
        st.session_state.db = db
        st.session_state.vector_store = vs
    return st.session_state.analytics


def render_dashboard():
    st.markdown("""
    <style>
    .stat-card {
        background: rgba(30,41,59,0.7); backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 20px;
        box-shadow: 0 0 20px rgba(99,102,241,0.08);
        transition: all 0.2s;
    }
    .stat-card:hover { background: #1d2022; }
    .stat-card .stat-icon { font-size: 24px; margin-bottom: 8px; }
    .stat-card .stat-label { color: #c7c4d7; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
    .stat-card .stat-value { color: #e0e3e5; font-size: 28px; font-weight: 700; margin: 4px 0; }
    .stat-card .stat-sub { color: #89ceff; font-size: 12px; display: flex; align-items: center; gap: 4px; }
    .stat-card.best { border-left: 4px solid #89ceff; }
    .stat-card.weak { border-left: 4px solid #ffb4ab; }

    .focus-card {
        padding: 16px; border-radius: 12px;
        border-left: 4px solid #ffb4ab;
        background: rgba(239,68,68,0.05);
        margin-bottom: 12px;
    }
    .focus-card.tip {
        border-left-color: #89ceff;
        background: rgba(137,206,255,0.05);
    }
    .focus-card h4 { margin: 0 0 4px; font-size: 14px; font-weight: 700; color: #e0e3e5; }
    .focus-card p { margin: 0; font-size: 12px; color: #c7c4d7; }

    .topic-bar {
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom: 4px; font-size: 13px;
    }
    .topic-bar .name { color: #e0e3e5; font-weight: 500; }
    .topic-bar .pct { color: #89ceff; font-weight: 700; }
    .topic-track {
        height: 8px; background: #272a2c; border-radius: 4px;
        overflow: hidden; margin-bottom: 16px;
    }
    .topic-track .fill {
        height: 100%; border-radius: 4px;
        background: linear-gradient(90deg, #6366F1, #8B5CF6);
        transition: width 0.5s ease;
    }
    .topic-track .fill.weak { background: linear-gradient(90deg, #ef4444, #dc2626); }

    .drift-card {
        padding: 16px; border-radius: 12px;
        border-left: 4px solid #F59E0B;
        background: rgba(245,158,11,0.05);
        margin-bottom: 12px;
    }
    .drift-card.alert {
        border-left-color: #ef4444;
        background: rgba(239,68,68,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

    analytics = _get_analytics()
    user_id = st.session_state.user_id

    topic_data = analytics.get_topic_summary(user_id)
    weak = analytics.get_weakest_topics(user_id)

    st.markdown("<div style='margin-bottom:24px'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color:#e0e3e5;font-size:28px;font-weight:700;margin:0'>Interview Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#c7c4d7;font-size:14px;margin:4px 0 0'>Review your performance trends and AI insights.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    total_interviews = len(analytics.db.get_user_sessions(user_id)) if hasattr(analytics, 'db') else 0
    avg_score = 0
    best_topic = "—"
    best_pct = 0
    weak_topic = "—"
    weak_pct = 0
    if topic_data:
        scores = [t["avg_score"] for t in topic_data]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        best = max(topic_data, key=lambda t: t["avg_score"])
        best_topic = best["topic"]
        best_pct = round(best["avg_score"] / 10 * 100)
        if weak:
            wt = weak[0]
            weak_topic = wt["topic"]
            weak_pct = round(wt["avg_score"] / 10 * 100)

    stat_cols = st.columns(4)
    stats_data = [
        ("📊", "Total Interviews", str(total_interviews), f"+{total_interviews} completed"),
        ("📈", "Avg Score", f"{avg_score}/10", "Top performer" if avg_score >= 7 else "Keep improving"),
        ("🏆", "Best Topic", html_escape(best_topic), f"Mastery: {best_pct}%"),
        ("🎯", "Weakest Topic", html_escape(weak_topic), f"Mastery: {weak_pct}%" if weak_pct else "No data"),
    ]
    for i, col in enumerate(stat_cols):
        with col:
            icon, label, value, sub = stats_data[i]
            cls = "best" if i == 2 else ("weak" if i == 3 else "")
            st.markdown(f"""
            <div class="stat-card {cls}">
                <div class="stat-icon">{icon}</div>
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    chart_cols = st.columns(3)

    with chart_cols[0]:
        st.markdown('<div class="glass-card" style="margin-top:24px">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#e0e3e5;font-size:18px;font-weight:600;margin:0 0 16px'>Topic Performance</h3>", unsafe_allow_html=True)

        if topic_data:
            for t in topic_data:
                pct = round(t["avg_score"] / 10 * 100)
                is_weak = t["avg_score"] < 6.0
                st.markdown(f"**{t['topic']}** — {pct}%")
                st.progress(pct / 100)
        else:
            st.info("No topic data yet. Complete an interview session to see progress.")
        st.markdown('</div>', unsafe_allow_html=True)

    with chart_cols[1]:
        st.markdown('<div class="glass-card" style="margin-top:24px">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#e0e3e5;font-size:18px;font-weight:600;margin:0 0 16px'>Score Trend</h3>", unsafe_allow_html=True)

        trend_df = analytics.get_session_trend(user_id)
        if not trend_df.empty:
            trend_df["date"] = pd.to_datetime(trend_df["date"])
            trend_agg = trend_df.groupby("date")["score"].mean().reset_index()
            fig2 = px.line(
                trend_agg, x="date", y="score",
                markers=True, range_y=[0, 10],
                labels={"score": "Avg Score", "date": ""},
                title="",
            )
            fig2.update_layout(
                height=250, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c7c4d7", size=12),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            )
            fig2.update_traces(
                line=dict(color="#c0c1ff", width=3),
                marker=dict(size=8, color="#6366F1", line=dict(color="#fff", width=2)),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Complete interview sessions to see score trends.")
        st.markdown('</div>', unsafe_allow_html=True)

    with chart_cols[2]:
        st.markdown('<div class="glass-card" style="margin-top:24px">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#e0e3e5;font-size:18px;font-weight:600;margin:0 0 16px'>Skill Radar</h3>", unsafe_allow_html=True)

        if topic_data:
            categories = [t["topic"] for t in topic_data]
            values = [round(t["avg_score"], 1) for t in topic_data]
            radar_fig = create_radar_chart(categories, values, "Overall Skills")
            st.plotly_chart(radar_fig, use_container_width=True)
        else:
            st.info("Complete interviews to see your skill radar.")
        st.markdown('</div>', unsafe_allow_html=True)

    bottom_cols = st.columns([1, 2])

    with bottom_cols[0]:
        st.markdown('<div style="margin-top:24px">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#e0e3e5;font-size:18px;font-weight:600;margin:0 0 16px'>Focus Areas</h3>", unsafe_allow_html=True)

        if weak:
            for w in weak:
                st.warning(
                    f"**{w['topic']}** — Avg score {w['avg_score']:.1f}/10 "
                    f"over {w['total_answers']} answers. Focus on improving this area."
                )
        else:
            st.success("Great Progress — No weak areas detected! Keep up the good work.")

        st.markdown("**Drift Monitoring**")
        try:
            drift_monitor = DriftMonitor(analytics.db)
            drift_result = drift_monitor.check_drift(user_id)
            if drift_result.get("drifting"):
                st.error(
                    f"**Score Drift Detected** — Z-score: {drift_result.get('z_score', 0):.2f}\n\n"
                    f"Recent avg: {drift_result.get('recent_avg', 0):.1f} vs Overall: {drift_result.get('overall_avg', 0):.1f}\n\n"
                    f"{drift_result.get('message', '')}"
                )
            else:
                st.success(
                    f"Scores stable (Z: {drift_result.get('z_score', 0):.2f}). "
                    f"Recent avg: {drift_result.get('recent_avg', 0):.1f}"
                )
        except Exception:
            st.info("Drift monitoring requires session data.")

        st.info("Review past low-score answers to identify patterns in your responses.")
        st.markdown('</div>', unsafe_allow_html=True)

    with bottom_cols[1]:
        emotion_history = st.session_state.get("emotion_history", [])
        vision_history = st.session_state.get("vision_history", [])

        if emotion_history or vision_history:
            st.markdown('<div style="margin-top:24px">', unsafe_allow_html=True)

            with st.expander("📢 Communication Analytics", expanded=True):
                if emotion_history:
                    conf_scores = [e["confidence_score"] for e in emotion_history]
                    filler_counts = [e["filler_count"] for e in emotion_history]

                    fig_conf = go.Figure()
                    fig_conf.add_trace(go.Scatter(
                        y=conf_scores, mode="lines+markers",
                        name="Confidence", line=dict(color="#10b981", width=3),
                        marker=dict(size=6),
                    ))
                    fig_conf.add_trace(go.Scatter(
                        y=filler_counts, mode="lines+markers",
                        name="Fillers", line=dict(color="#ef4444", width=3),
                        marker=dict(size=6),
                    ))
                    fig_conf.update_layout(
                        title=dict(text="Confidence & Fillers", font=dict(color="#e0e3e5", size=14)),
                        height=200, margin=dict(l=0, r=0, t=30, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#c7c4d7", size=11),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                        legend=dict(orientation="h", y=1.1, font=dict(color="#c7c4d7")),
                    )
                    st.plotly_chart(fig_conf, use_container_width=True)

                    ccols = st.columns(2)
                    with ccols[0]:
                        avg_conf = sum(conf_scores) / len(conf_scores)
                        st.metric("Avg Confidence", f"{avg_conf:.1f}/10")
                    with ccols[1]:
                        total_fillers = sum(filler_counts)
                        st.metric("Total Fillers", str(total_fillers))

                if vision_history:
                    eye_contact_pct = sum(1 for v in vision_history if v["eye_contact"]) / len(vision_history) * 100
                    avg_yaw = sum(abs(v["head_pose"]["yaw"]) for v in vision_history) / len(vision_history)

                    fig_eye = go.Figure()
                    fig_eye.add_trace(go.Scatter(
                        y=[v["eye_contact"] for v in vision_history],
                        mode="lines", name="Eye Contact",
                        line=dict(color="#3b82f6", width=3),
                    ))
                    fig_eye.update_layout(
                        title=dict(text="Eye Contact Over Time", font=dict(color="#e0e3e5", size=14)),
                        height=150, margin=dict(l=0, r=0, t=30, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#c7c4d7", size=11),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(tickvals=[0, 1], ticktext=["No", "Yes"], showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_eye, use_container_width=True)

                    vcols = st.columns(2)
                    with vcols[0]:
                        st.metric("Eye Contact", f"{eye_contact_pct:.0f}%")
                    with vcols[1]:
                        st.metric("Avg Head Yaw", f"{avg_yaw:.1f}°")

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card" style="margin-top:16px">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#e0e3e5;font-size:16px;font-weight:600;margin:0 0 12px'>📋 Coach's Recommendations</h3>", unsafe_allow_html=True)
        recs = analytics.get_recommendations(user_id)
        if recs:
            for rec in recs:
                st.info(rec)
        else:
            st.info("Complete more interviews to get personalized recommendations.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card" style="margin-top:16px">', unsafe_allow_html=True)
        with st.expander("📝 Past Low-Score Answers", expanded=False):
            low_answers = analytics.get_low_score_answers(user_id)
            if low_answers:
                for ans in low_answers:
                    st.markdown(f"**Answer:** {ans['text'][:300]}...")
                    st.caption(
                        f"Topic: {ans['metadata'].get('topic', 'N/A')} | "
                        f"Score: {ans['metadata'].get('score', 'N/A')}"
                    )
            else:
                st.info("No low-score answers recorded yet.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card" style="margin-top:16px">', unsafe_allow_html=True)
        with st.expander("📄 Download Session Report", expanded=False):
            sessions = analytics.db.get_user_sessions(user_id)
            if sessions:
                for sess in sessions[:5]:
                    answers = analytics.db.get_session_answers(sess["id"])
                    avg = round(sum(a["score"] for a in answers) / len(answers), 1) if answers else 0
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**Session #{sess['id']}** — {len(answers)} questions — Avg: {avg}/10")
                    with cols[1]:
                        if st.button("Generate Report", key=f"report_{sess['id']}"):
                            try:
                                gen = ReportGenerator()
                                path = gen.generate_session_report(sess["id"], analytics.db)
                                st.success(f"Report saved: {path}")
                            except Exception as e:
                                st.error(f"Failed: {e}")
            else:
                st.info("No sessions to report on.")
        st.markdown('</div>', unsafe_allow_html=True)
