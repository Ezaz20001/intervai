import json
import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.database.db import Database
from backend.vector_store.store import VectorStore
from backend.llm.service import LLMService
from backend.feedback.engine import FeedbackEngine
from backend.orchestrator.interviewer import InterviewOrchestrator
from backend.analytics.service import AnalyticsService
from backend.ingestion.pipeline import IngestionPipeline
from backend.evaluation.drift_monitor import DriftMonitor
from backend.reports.pdf_report import ReportGenerator
from backend import config
from backend.security import (
    validate_user_id,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    safe_path,
    require_api_key,
    rate_limit,
    session_manager,
    load_api_keys_from_env,
    cleanup_expired_tokens,
)

app = FastAPI(title="Mock Interview AI API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


db = Database()
vector_store = VectorStore()
llm = LLMService()
feedback_engine = FeedbackEngine()
analytics = AnalyticsService(db, vector_store)
drift_monitor = DriftMonitor(db)
report_generator = ReportGenerator()

load_api_keys_from_env()


@app.post("/upload-docs")
async def upload_docs(
    request: Request,
    user_id: str = Form(...),
    cv: UploadFile = File(...),
    jd: UploadFile = File(...),
):
    rate_limit(request)
    require_api_key(request)
    user_id = validate_user_id(user_id)

    for f in [cv, jd]:
        if not f.filename:
            raise HTTPException(status_code=400, detail="File name is required.")
        validate_file_extension(f.filename)
        content = await f.read()
        validate_file_size(len(content))
        await f.seek(0)

    user_dir = Path(config.UPLOAD_DIR) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    cv_name = sanitize_filename(cv.filename)
    jd_name = sanitize_filename(jd.filename)

    cv_path = safe_path(user_dir, cv_name)
    jd_path = safe_path(user_dir, jd_name)

    with open(cv_path, "wb") as f:
        f.write(await cv.read())
    with open(jd_path, "wb") as f:
        f.write(await jd.read())

    pipeline = IngestionPipeline(vector_store)
    cv_ids = pipeline.ingest(str(cv_path), user_id, "cv", "experience")
    jd_ids = pipeline.ingest(str(jd_path), user_id, "jd", "requirements")

    return {
        "message": "Documents ingested",
        "user_id": user_id,
        "cv_chunks": len(cv_ids),
        "jd_chunks": len(jd_ids),
    }


@app.post("/start-session")
async def start_session(
    request: Request,
    user_id: str = Form(...),
    role_title: Optional[str] = Form(""),
):
    rate_limit(request)
    require_api_key(request)
    user_id = validate_user_id(user_id)

    orch = InterviewOrchestrator(llm, vector_store, db, feedback_engine)
    orch.start_session(user_id, role_title or "")
    session_manager.create(orch.session_id, user_id, orch)

    question = orch.next_question()
    cited = orch.cited_entries
    return {
        "session_id": orch.session_id,
        "question": question,
        "question_number": 1,
        "total_questions": config.SESSION_QUESTION_LIMIT,
        "cited_entries": cited,
    }


@app.post("/chat")
async def chat(
    request: Request,
    session_id: int = Form(...),
    user_answer: str = Form(...),
    auth_user_id: str = Form(...),
):
    rate_limit(request)
    require_api_key(request)
    auth_user_id = validate_user_id(auth_user_id)

    if len(user_answer) > 5000:
        raise HTTPException(status_code=400, detail="Answer too long. Maximum 5000 characters.")

    orch = session_manager.get(session_id, user_id=auth_user_id)
    if not orch:
        existing = db.get_session(session_id)
        if existing and existing["ended_at"]:
            return {"message": "Session already ended", "session_id": session_id}
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    if not orch.is_active:
        session_manager.remove(session_id)
        raise HTTPException(status_code=400, detail="Session has ended")

    result = orch.submit_answer(user_answer)

    if result.get("finished"):
        session_manager.remove(session_id)
        return {"finished": True, "session_id": session_id, **result}

    next_q = orch.next_question()
    return {
        "finished": False,
        "session_id": session_id,
        "question": next_q,
        "cited_entries": orch.cited_entries,
        **result,
    }


@app.post("/chat-stream")
async def chat_stream(
    request: Request,
    session_id: int = Form(...),
    user_answer: str = Form(...),
    auth_user_id: str = Form(...),
):
    rate_limit(request)
    require_api_key(request)
    auth_user_id = validate_user_id(auth_user_id)

    orch = session_manager.get(session_id, user_id=auth_user_id)
    if not orch:
        raise HTTPException(status_code=404, detail="Session not found")

    def generate_events():
        result = orch.submit_answer(user_answer)
        yield f"data: {json.dumps({'type': 'grading', 'data': result})}\n\n"

        if not result.get("finished") and not result.get("blocked"):
            next_q = orch.next_question()
            yield f"data: {json.dumps({'type': 'next_question', 'data': {'question': next_q, 'cited_entries': orch.cited_entries}})}\n\n"

        if result.get("finished"):
            session_manager.remove(session_id)
            yield f"data: {json.dumps({'type': 'session_complete', 'data': {'session_id': session_id}})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/stop-session")
async def stop_session(
    request: Request,
    session_id: int = Form(...),
    auth_user_id: str = Form(...),
):
    rate_limit(request)
    require_api_key(request)
    auth_user_id = validate_user_id(auth_user_id)

    orch = session_manager.get(session_id, user_id=auth_user_id)
    if not orch:
        existing = db.get_session(session_id)
        if existing and existing["ended_at"]:
            return {"message": "Session already ended", "session_id": session_id}
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    orch.end_session()
    session_manager.remove(session_id)

    answers = db.get_session_answers(session_id)
    avg_score = round(sum(a["score"] for a in answers) / len(answers), 1) if answers else 0

    return {
        "message": "Session ended",
        "session_id": session_id,
        "total_answers": len(answers),
        "average_score": avg_score,
    }


@app.get("/progress/{user_id}")
async def get_progress(request: Request, user_id: str):
    rate_limit(request)
    require_api_key(request)
    user_id = validate_user_id(user_id)

    topics = analytics.get_topic_summary(user_id)
    weak = analytics.get_weakest_topics(user_id)
    recommendations = analytics.get_recommendations(user_id)
    sessions = db.get_user_sessions(user_id)

    total_answers = 0
    for s in sessions:
        total_answers += len(db.get_session_answers(s["id"]))

    overall_avg = 0.0
    if topics:
        total_weighted = sum(t["avg_score"] * t["total_answers"] for t in topics)
        total_count = sum(t["total_answers"] for t in topics)
        if total_count > 0:
            overall_avg = round(total_weighted / total_count, 1)

    return {
        "user_id": user_id,
        "overall_avg_score": overall_avg,
        "total_sessions": len(sessions),
        "total_answers": total_answers,
        "topics": topics,
        "weakest_areas": weak,
        "recommendations": recommendations,
    }


@app.get("/drift/{user_id}")
async def get_drift(request: Request, user_id: str):
    rate_limit(request)
    require_api_key(request)
    user_id = validate_user_id(user_id)
    result = drift_monitor.check_drift(user_id)
    return result


@app.get("/drift")
async def get_all_drift(request: Request):
    rate_limit(request)
    require_api_key(request)
    return drift_monitor.get_all_users_drift()


@app.get("/report/{session_id}")
async def get_report(request: Request, session_id: int):
    rate_limit(request)
    require_api_key(request)
    try:
        # NOTE: Generated report files should be cleaned up periodically
        # to avoid disk space exhaustion. Consider a cron job or background task.
        report_generator.generate_session_report(session_id, db)
        return {"message": "Report generated", "session_id": session_id}
    except Exception:
        logging.exception("Report generation failed")
        raise HTTPException(status_code=500, detail="Report generation failed. Please try again.")
