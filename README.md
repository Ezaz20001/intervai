<div align="center">

# IntervAI — AI Mock Interviewer & Grader

**An end-to-end AI-powered mock interview platform with STAR-format grading, RAG-powered question generation, and real-time performance analytics.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-40%20passing-brightgreen.svg)](#testing)

</div>

---

## What This Does

IntervAI conducts realistic mock interviews by reading your resume and job description, generating personalized questions, grading your answers on **STAR format**, **coherence**, and **keyword coverage**, then providing actionable feedback — all in real time.

### Key Features

| Feature | Description |
|---------|-------------|
| **STAR Grader** | Evaluates answers on Situation-Task-Action-Result structure, coherence, and job keyword coverage |
| **RAG Question Generation** | Retrieves your resume skills + projects separately to generate personalized questions |
| **Cross-Encoder Reranking** | Reranks resume bullets by relevance to each question using `ms-marco-MiniLM-L-6-v2` |
| **Hybrid Retrieval** | Separately retrieves skills, projects, and JD requirements for context-aware grading |
| **Input Guardrails** | Filters prompt injection attempts and off-topic responses before they reach the LLM |
| **Drift Monitoring** | Z-score based detection of sudden score drops across user sessions |
| **Radar Charts** | Real-time skill breakdown visualization (STAR / Coherence / Keywords) |
| **Cited Resume Entries** | Shows which resume chunks generated each question for transparency |
| **Countdown Timer** | Simulates real interview pressure with visual urgency indicators |
| **PDF Reports** | Generates downloadable dark-themed interview reports with per-question breakdowns |
| **Voice I/O** | Speech-to-text input and text-to-speech output for natural interview flow |
| **Face/Hand Tracking** | MediaPipe-based eye contact and gesture analysis during interviews |
| **Sentiment Analysis** | Real-time VADER-based emotion tracking with confidence scoring |
| **4-bit Local LLM** | Optional Mistral/Llama 7B via bitsandbytes quantization with Groq fallback |
| **Celery Workers** | Async PDF parsing with Redis-backed task queue |
| **Full Docker Stack** | API + Streamlit + Celery + Redis + PostgreSQL + Nginx |
| **50-Case Test Harness** | Pre-scored answers with MAE validation for grader accuracy |

---

## Architecture

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────┐
│  Nginx  │────▶│ Streamlit│────▶│   FastAPI    │────▶│   LLM    │
│  :80    │     │  :8501   │     │    :8000     │     │ (Groq/   │
└─────────┘     └─────────┘     └──────┬───────┘     │  Local)  │
                                       │              └──────────┘
                                       ▼
                                ┌──────────────┐
                                │   Celery     │
                                │   Workers    │
                                └──────┬───────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                   ▼
             ┌────────────┐   ┌──────────────┐   ┌──────────────┐
             │  ChromaDB  │   │   PostgreSQL  │   │    Redis     │
             │  (Vector)  │   │  (Sessions)   │   │  (Broker)    │
             └────────────┘   └──────────────┘   └──────────────┘
```

---

## Tech Stack

**AI/ML:** Groq API (Llama 3.1), Sentence-BERT, Cross-Encoders, VADER Sentiment, MediaPipe, bitsandbytes (4-bit quantization)

**Backend:** FastAPI, Celery, SQLAlchemy, ChromaDB, PostgreSQL, Redis, SQLite

**Frontend:** Streamlit, Plotly (radar/line charts), custom CSS (glassmorphism)

**Infra:** Docker Compose, Nginx reverse proxy, Uvicorn ASGI

**Testing:** pytest (40 tests), custom 50-case grader test harness

---

## Quick Start

### Local Development

```bash
git clone https://github.com/Ezaz20001/intervai.git
cd intervai
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt

# Set your Groq API key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Run
streamlit run frontend/app.py
```

### Docker (Full Stack)

```bash
# Set secrets in .env
echo "GROQ_API_KEY=gsk_your_key" >> .env
echo "POSTGRES_PASSWORD=your_secure_password" >> .env
echo "REDIS_PASSWORD=your_redis_password" >> .env

docker-compose up --build
```

Services: Nginx (`:80`), Streamlit (`:8501`), FastAPI (`:8000`), Redis (`:6379`), PostgreSQL (`:5432`), Celery Worker

---

## Project Structure

```
intervai/
├── backend/
│   ├── api.py                  # FastAPI REST API + SSE streaming
│   ├── config.py               # Central configuration
│   ├── security.py             # Auth, rate limiting, session management
│   ├── celery_app.py           # Celery configuration
│   ├── llm/
│   │   ├── service.py          # Groq API + dual-persona prompting
│   │   └── local_llm.py        # 4-bit quantized local model
│   ├── rag/
│   │   ├── hybrid_retriever.py # Skills/Projects separate retrieval
│   │   └── reranker.py         # Cross-encoder reranking
│   ├── grader/
│   │   └── star_grader.py      # STAR + Coherence + Keyword grading
│   ├── evaluation/
│   │   ├── test_harness.py     # 50 pre-scored answer test suite
│   │   └── drift_monitor.py    # Z-score drift detection
│   ├── guardrails/
│   │   └── input_guardrail.py  # Prompt injection + off-topic filter
│   ├── ingestion/
│   │   ├── pipeline.py         # Document ingestion pipeline
│   │   ├── chunker.py          # Semantic chunking
│   │   ├── entities.py         # Resume entity extraction
│   │   └── loader.py           # PDF/DOCX/TXT loading
│   ├── vector_store/
│   │   └── store.py            # ChromaDB + HuggingFace embeddings
│   ├── database/
│   │   ├── db.py               # SQLite (auto-migrating)
│   │   ├── postgres_db.py      # PostgreSQL adapter
│   │   └── models.py           # Schema definitions
│   ├── reports/
│   │   └── pdf_report.py       # PDF report generation
│   ├── finetuning/
│   │   ├── dataset.py          # Good/Bad answer curation
│   │   └── qlora.py            # QLoRA fine-tuning pipeline
│   ├── orchestrator/
│   │   └── interviewer.py      # Core session orchestration
│   ├── feedback/
│   │   └── engine.py           # Feedback storage + vector persistence
│   ├── emotion/
│   │   └── analyzer.py         # VADER sentiment + filler detection
│   ├── vision/
│   │   └── analyzer.py         # MediaPipe face/hand tracking
│   ├── voice/
│   │   ├── tts.py              # Google Text-to-Speech
│   │   └── stt.py              # Speech-to-Text
│   └── workers/
│       └── pdf_worker.py       # Celery async PDF task
├── frontend/
│   ├── app.py                  # Streamlit entry point + CSS
│   ├── pages/
│   │   ├── auth.py             # Login / registration
│   │   ├── interview.py        # Interview session UI
│   │   └── dashboard.py        # Analytics dashboard
│   ├── components/
│   │   ├── radar_chart.py      # Plotly radar charts
│   │   ├── countdown_timer.py  # Interview pressure timer
│   │   └── pdf_report.py       # Report generation wrapper
│   └── utils/
│       ├── session.py          # Session state management
│       └── ingest.py           # Document upload handling
├── tests/                      # 40 tests (10 test files)
├── docker/
│   └── nginx/nginx.conf        # Reverse proxy config
├── figma/                      # Design mockups
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile                  # Streamlit container
├── Dockerfile.api              # FastAPI container
└── requirements.txt
```

---

## Grading System

The grader evaluates each answer on three dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **STAR Format** | 40% | Did the answer include Situation, Task, Action, and Result? |
| **Coherence** | 30% | Is the answer logically structured and clearly communicated? |
| **Keywords** | 30% | Does the answer use job-relevant technical terms and concepts? |

Each dimension is scored 1-10. The overall score is a weighted average with personalized feedback on strengths, improvements, and a rewritten "better phrasing" of the answer.

---

## Security

- **29 vulnerabilities** found and fixed across CRITICAL/HIGH/MEDIUM severity
- Rate limiting with sliding window per client IP
- Input guardrails against prompt injection and off-topic queries
- File upload validation (extension, size, path traversal protection)
- CORS validation, CSP and Permissions-Policy headers via Nginx
- Audit logging for auth events, failed attempts, and rate limit hits
- SQL injection prevention via parameterized queries + column whitelist
- XSS prevention via HTML escaping of user-generated content

---

## Testing

```bash
pytest tests/ -v
```

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_star_grader.py` | 4 | Grading prompt, JSON parsing, field validation |
| `test_guardrails.py` | 5 | Injection detection, off-topic, validation |
| `test_hybrid_retriever.py` | 3 | Skills/projects retrieval, combined context |
| `test_drift_monitor.py` | 3 | Stable scores, drift detection, empty history |
| `test_entities.py` | 4 | Skills, projects, education extraction |
| `test_reranker.py` | 2 | Sorting, top-k respect |
| `test_semantic_chunker.py` | 4 | Section boundaries, splitting logic |
| `test_pdf_report.py` | 2 | Report generation, file creation |
| `test_chunker.py` | 4 | Text chunking, order preservation |
| `test_emotion.py` | 6 | Sentiment, fillers, confidence scoring |
| `test_loader.py` | 3 | PDF/DOCX/TXT loading, error handling |
| **Total** | **40** | |

---

## Deployment

### Streamlit Community Cloud (Free)

1. Fork this repo on GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set `frontend/app.py` as main file
4. Add `GROQ_API_KEY` in Advanced Settings → Secrets
5. Deploy → get your permanent URL

### Docker Compose (Production)

```bash
docker-compose up --build -d
```

Access via Nginx at `http://localhost` (Streamlit + API behind reverse proxy).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | (required) | Groq API key for LLM inference |
| `USE_LOCAL_LLM` | `false` | Enable 4-bit quantized local model |
| `LOCAL_LLM_MODEL` | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace model ID |
| `SESSION_QUESTION_LIMIT` | `5` | Questions per interview session |
| `COUNTDOWN_SECONDS` | `120` | Timer per question (seconds) |
| `USE_POSTGRES` | `false` | Use PostgreSQL instead of SQLite |
| `POSTGRES_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery broker |
| `DRIFT_Z_THRESHOLD` | `2.0` | Z-score threshold for drift alerts |
| `CROSS_ENCODER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranking model |

---

## License

MIT
