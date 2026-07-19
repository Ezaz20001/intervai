from typing import List

from backend.ingestion.loader import load_document
from backend.ingestion.chunker import semantic_chunk_text
from backend.ingestion.entities import ResumeEntityExtractor
from backend.vector_store.store import VectorStore


class IngestionPipeline:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.entity_extractor = ResumeEntityExtractor()

    def ingest(
        self,
        file_path: str,
        user_id: str,
        source_type: str,
        topic: str = "",
    ) -> List[str]:
        text = load_document(file_path)
        chunks = semantic_chunk_text(text)
        entities = self.entity_extractor.extract(text)
        entity_metadata = self.entity_extractor.extract_as_metadata(text)

        metadatas = []
        for i, chunk in enumerate(chunks):
            meta = {
                "source": source_type,
                "user_id": user_id,
                "topic": topic,
                "date": __import__("datetime").datetime.now().isoformat(),
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            meta.update(entity_metadata)

            chunk_lower = chunk.lower()
            if any(skill.lower() in chunk_lower for skill in entities.get("skills", [])):
                meta["contains_skills"] = "true"
            if any(proj.lower() in chunk_lower for proj in entities.get("projects", [])):
                meta["contains_projects"] = "true"
            if entities.get("experience"):
                meta["contains_experience"] = "true"

            metadatas.append(meta)

        ids = self.vector_store.add_documents(chunks, metadatas)
        return ids
