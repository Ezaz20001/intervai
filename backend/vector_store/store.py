import os
os.environ["TQDM_DISABLE"] = "1"

from typing import List, Dict, Any, Optional

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

from backend import config


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
        )
        self.collection = self.client.get_or_create_collection(
            name="interview_docs",
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def add_documents(
        self, texts: List[str], metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        embeddings = self.embedder.embed_documents(texts)
        ids = [f"doc_{abs(hash(t))}_{i}" for i, t in enumerate(texts)]
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        return ids

    def similarity_search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_query(query)
        where_clause = None
        if filter_metadata:
            conditions = [{k: {"$eq": v}} for k, v in filter_metadata.items()]
            where_clause = conditions[0] if len(conditions) == 1 else {"$and": conditions}
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
        )
        docs = []
        for i in range(len(results["ids"][0])):
            docs.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                }
            )
        return docs

    def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        user_id: str = "",
        source_filter: Optional[str] = None,
        contains_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = [{"user_id": {"$eq": user_id}}]
        if source_filter:
            conditions.append({"source": {"$eq": source_filter}})
        if contains_filter:
            conditions.append({contains_filter: {"$eq": "true"}})

        where_clause = conditions[0] if len(conditions) == 1 else {"$and": conditions}

        query_embedding = self.embedder.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
        )
        docs = []
        for i in range(len(results["ids"][0])):
            docs.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                }
            )
        return docs

    def search_skills(self, query: str, user_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.hybrid_search(query, n_results, user_id, "cv", "contains_skills")

    def search_projects(self, query: str, user_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.hybrid_search(query, n_results, user_id, "cv", "contains_projects")

    def search_experience(self, query: str, user_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.hybrid_search(query, n_results, user_id, "cv", "contains_experience")

    def delete_user_docs(self, user_id: str):
        self.collection.delete(where={"user_id": user_id})

    def embed_query(self, query: str) -> List[float]:
        return self.embedder.embed_query(query)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(texts)
