import re
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

SENTENCE_BOUNDARIES = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
SECTION_HEADERS = re.compile(
    r'\n(?=(?:EXPERIENCE|EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|'
    r'WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|TECHNICAL SKILLS|'
    r'SUMMARY|OBJECTIVE|AWARDS|PUBLICATIONS|REFERENCES)\b)',
    re.IGNORECASE,
)


def _find_section_breaks(text: str) -> List[int]:
    breaks = []
    for match in SECTION_HEADERS.finditer(text):
        breaks.append(match.start())
    return breaks


def _preserve_sections(text: str) -> List[str]:
    sections = SECTION_HEADERS.split(text)
    return [s.strip() for s in sections if s.strip()]


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    sections = _preserve_sections(text)
    all_chunks = []

    for section in sections:
        if len(section) <= chunk_size:
            all_chunks.append(section)
            continue

        sentences = SENTENCE_BOUNDARIES.split(section)
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            s_len = len(sentence)
            if current_len + s_len > chunk_size and current_chunk:
                all_chunks.append(" ".join(current_chunk))
                overlap_start = max(0, len(current_chunk) - max(1, chunk_overlap // 50))
                current_chunk = current_chunk[overlap_start:]
                current_len = sum(len(s) for s in current_chunk)
            current_chunk.append(sentence)
            current_len += s_len

        if current_chunk:
            all_chunks.append(" ".join(current_chunk))

    if not all_chunks:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        all_chunks = splitter.split_text(text)

    return all_chunks


def semantic_chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 150,
    min_chunk_size: int = 100,
) -> List[str]:
    sections = _preserve_sections(text)
    all_chunks = []

    for section in sections:
        if len(section) <= chunk_size:
            all_chunks.append(section)
            continue

        sentences = SENTENCE_BOUNDARIES.split(section)
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            s_len = len(sentence)

            if current_len + s_len > chunk_size and current_chunk:
                chunk_text_str = " ".join(current_chunk)
                if current_len >= min_chunk_size:
                    all_chunks.append(chunk_text_str)
                overlap_start = max(0, len(current_chunk) - max(1, chunk_overlap // 60))
                current_chunk = current_chunk[overlap_start:]
                current_len = sum(len(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_len += s_len

        if current_chunk:
            chunk_text_str = " ".join(current_chunk)
            if len(current_chunk) > 1 and current_len < min_chunk_size and all_chunks:
                all_chunks[-1] = all_chunks[-1] + " " + chunk_text_str
            else:
                all_chunks.append(chunk_text_str)

    if not all_chunks:
        return chunk_text(text, chunk_size, chunk_overlap)

    return all_chunks
