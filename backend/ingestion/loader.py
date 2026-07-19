from pathlib import Path
from typing import List


def load_pdf(file_path: str) -> str:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join(p.page_content for p in pages)


def load_docx(file_path: str) -> str:
    from langchain_community.document_loaders import Docx2txtLoader
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    return "\n".join(d.page_content for d in docs)


def load_txt(file_path: str) -> str:
    from langchain_community.document_loaders import TextLoader
    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()
    return "\n".join(d.page_content for d in docs)


def load_document(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext == ".txt":
        return load_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
