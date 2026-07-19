import os
from datetime import datetime
from typing import Optional

from backend.database.db import Database


class ReportGenerator:
    def generate_session_report(
        self,
        session_id: int,
        db: Database,
        output_path: Optional[str] = None,
    ) -> str:
        session = db.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        answers = db.get_session_answers(session_id)

        if output_path is None:
            output_path = os.path.join(
                "data", "reports", f"report_{session_id}.pdf"
            )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            return self._generate_pdf(session, answers, output_path)
        except ImportError:
            return self._generate_text(session, answers, output_path)

    def _generate_pdf(
        self, session: dict, answers: list, output_path: str
    ) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        dark_bg = colors.HexColor("#1a1a2e")
        accent = colors.HexColor("#e94560")
        light_text = colors.HexColor("#eaeaea")
        medium_text = colors.HexColor("#b0b0b0")

        title_style = ParagraphStyle(
            "DarkTitle", parent=styles["Title"],
            textColor=accent, fontSize=24, spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DarkSubtitle", parent=styles["Normal"],
            textColor=medium_text, fontSize=11, spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "DarkHeading", parent=styles["Heading2"],
            textColor=accent, fontSize=14, spaceBefore=16, spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "DarkBody", parent=styles["Normal"],
            textColor=light_text, fontSize=10, leading=14,
        )
        small_style = ParagraphStyle(
            "DarkSmall", parent=styles["Normal"],
            textColor=medium_text, fontSize=8,
        )

        story.append(Paragraph("IntervAI Interview Report", title_style))
        story.append(HRFlowable(width="100%", color=accent, thickness=2))
        story.append(Spacer(1, 12))

        started = session.get("started_at", "N/A")
        ended = session.get("ended_at", "In Progress")
        duration = ""
        if session.get("ended_at"):
            try:
                s = datetime.fromisoformat(session["started_at"])
                e = datetime.fromisoformat(session["ended_at"])
                mins = int((e - s).total_seconds() / 60)
                duration = f"{mins} minutes"
            except (ValueError, TypeError):
                duration = "N/A"

        summary_data = [
            ["Session ID", str(session["id"])],
            ["User", session.get("user_id", "N/A")],
            ["Job Role", session.get("job_role", "N/A")],
            ["Started", started],
            ["Ended", ended],
            ["Duration", duration],
            ["Questions Answered", str(len(answers))],
        ]
        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), dark_bg),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (0, -1), accent),
            ("TEXTCOLOR", (1, 0), (1, -1), light_text),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333355")),
        ]))
        story.append(Paragraph("Session Summary", heading_style))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        if answers:
            story.append(Paragraph("Question Breakdown", heading_style))
            qa_data = [["#", "Question", "Score", "Topic"]]
            for i, a in enumerate(answers, 1):
                q = a["question"][:80] + ("..." if len(a["question"]) > 80 else "")
                qa_data.append([
                    str(i),
                    Paragraph(q, body_style),
                    str(a["score"]),
                    a.get("topic", ""),
                ])

            qa_table = Table(
                qa_data,
                colWidths=[0.4 * inch, 3.8 * inch, 0.6 * inch, 1.2 * inch],
            )
            qa_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#16213e")),
                ("TEXTCOLOR", (0, 1), (-1, -1), light_text),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333355")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(qa_table)
            story.append(Spacer(1, 20))

            total_score = sum(a["score"] for a in answers)
            avg_score = total_score / len(answers)
            story.append(Paragraph("Overall Score", heading_style))
            story.append(
                Paragraph(f"{avg_score:.1f} / 10 ({len(answers)} questions)", body_style)
            )
            story.append(Spacer(1, 12))

            topics = {}
            for a in answers:
                t = a.get("topic", "general")
                if t not in topics:
                    topics[t] = []
                topics[t].append(a["score"])

            if topics:
                story.append(Paragraph("Topic Breakdown", heading_style))
                topic_data = [["Topic", "Avg Score", "Count"]]
                for topic, scores in sorted(topics.items()):
                    topic_data.append([
                        topic,
                        f"{sum(scores)/len(scores):.1f}",
                        str(len(scores)),
                    ])
                topic_table = Table(topic_data, colWidths=[2 * inch, 1.5 * inch, 1 * inch])
                topic_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), accent),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), light_text),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333355")),
                ]))
                story.append(topic_table)
                story.append(Spacer(1, 20))

            strengths = []
            improvements = []
            for a in answers:
                fb = a.get("feedback_text", "")
                if "strength" in fb.lower() or a["score"] >= 7:
                    strengths.append(a.get("topic", "general"))
                if "improv" in fb.lower() or a["score"] <= 5:
                    improvements.append(a.get("topic", "general"))

            story.append(Paragraph("Strengths", heading_style))
            if strengths:
                for s in set(strengths):
                    story.append(Paragraph(f"  - {s}", body_style))
            else:
                story.append(Paragraph("  - No clear strengths identified yet", body_style))

            story.append(Paragraph("Areas for Improvement", heading_style))
            if improvements:
                for imp in set(improvements):
                    story.append(Paragraph(f"  - {imp}", body_style))
            else:
                story.append(Paragraph("  - Keep up the good work!", body_style))

        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", color=accent, thickness=1))
        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                small_style,
            )
        )

        doc.build(story)
        return output_path

    def _generate_text(
        self, session: dict, answers: list, output_path: str
    ) -> str:
        txt_path = output_path.replace(".pdf", ".txt")
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)

        lines = []
        lines.append("=" * 60)
        lines.append("       IntervAI Interview Report")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Session ID:   {session['id']}")
        lines.append(f"User:         {session.get('user_id', 'N/A')}")
        lines.append(f"Job Role:     {session.get('job_role', 'N/A')}")
        lines.append(f"Started:      {session.get('started_at', 'N/A')}")
        lines.append(f"Ended:        {session.get('ended_at', 'In Progress')}")
        lines.append(f"Questions:    {len(answers)}")
        lines.append("")

        if answers:
            total = 0
            for i, a in enumerate(answers, 1):
                lines.append(f"--- Question {i} ---")
                lines.append(f"Q: {a['question']}")
                lines.append(f"A: {a['answer']}")
                lines.append(f"Score: {a['score']}/10  Topic: {a.get('topic', 'N/A')}")
                lines.append(f"Feedback: {a.get('feedback_text', '')}")
                lines.append("")
                total += a["score"]

            avg = total / len(answers)
            lines.append("=" * 60)
            lines.append(f"Overall Score: {avg:.1f} / 10")
            lines.append("=" * 60)

        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return txt_path
