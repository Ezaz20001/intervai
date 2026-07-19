from pathlib import Path

import streamlit as st

from backend.ingestion.pipeline import IngestionPipeline
from backend.vector_store.store import VectorStore
from backend import config
from backend.security import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    safe_path,
)


def ingest_documents(user_id: str, cv_file, jd_file) -> VectorStore:
    for f in [cv_file, jd_file]:
        if not f.name:
            raise ValueError("File name is required.")
        validate_file_extension(f.name)
        content = f.getvalue()
        validate_file_size(len(content))

    user_dir = Path(config.UPLOAD_DIR) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    cv_name = sanitize_filename(cv_file.name)
    jd_name = sanitize_filename(jd_file.name)

    cv_path = safe_path(user_dir, cv_name)
    jd_path = safe_path(user_dir, jd_name)

    with open(cv_path, "wb") as f:
        f.write(cv_file.getbuffer())
    with open(jd_path, "wb") as f:
        f.write(jd_file.getbuffer())

    vs = VectorStore()
    vs.delete_user_docs(user_id)
    pipeline = IngestionPipeline(vs)
    pipeline.ingest(str(cv_path), user_id, "cv", "experience")
    pipeline.ingest(str(jd_path), user_id, "jd", "requirements")

    st.session_state.vector_store = vs
    return vs
