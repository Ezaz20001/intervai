from backend.celery_app import app
from backend.vector_store.store import VectorStore
from backend.ingestion.pipeline import IngestionPipeline


@app.task(name="workers.parse_pdf_async", bind=True, max_retries=2)
def parse_pdf_async(self, file_path: str, user_id: str) -> dict:
    try:
        vector_store = VectorStore()
        pipeline = IngestionPipeline(vector_store)
        ids = pipeline.ingest(
            file_path=file_path,
            user_id=user_id,
            source_type="cv",
            topic="resume",
        )
        return {
            "status": "success",
            "chunk_count": len(ids),
            "file_path": file_path,
            "user_id": user_id,
        }
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "chunk_count": 0,
                "file_path": file_path,
                "error": str(exc),
            }
