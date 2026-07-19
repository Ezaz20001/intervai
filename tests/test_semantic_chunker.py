from backend.ingestion.chunker import semantic_chunk_text


def test_respects_section_boundaries():
    text = (
        "SKILLS\nPython, JavaScript, Docker\n\n"
        "EXPERIENCE\nSenior Engineer at Acme Corp for five years"
    )
    chunks = semantic_chunk_text(text, chunk_size=100)
    assert len(chunks) >= 2
    has_skills = any("Python" in c for c in chunks)
    has_experience = any("Engineer" in c for c in chunks)
    assert has_skills
    assert has_experience


def test_single_section():
    text = "Short resume content with just a few lines of text about the candidate."
    chunks = semantic_chunk_text(text, chunk_size=500)
    assert len(chunks) == 1
    assert "candidate" in chunks[0]


def test_multiple_sections():
    text = (
        "SUMMARY\nExperienced software engineer with ten years in the field.\n\n"
        "SKILLS\nPython, Java, C++, Go, Rust, Docker, Kubernetes\n\n"
        "EDUCATION\nBachelor of Science in Computer Science from Stanford University\n\n"
        "EXPERIENCE\nWorked at Google and Meta as a senior software engineer"
    )
    chunks = semantic_chunk_text(text, chunk_size=200)
    assert len(chunks) >= 3


def test_long_section_split():
    sentences = ". ".join(
        f"This is sentence number {i} describing the candidate's extensive experience in various domains."
        for i in range(20)
    )
    text = f"EXPERIENCE\n{sentences}"
    chunks = semantic_chunk_text(text, chunk_size=200, min_chunk_size=50)
    assert len(chunks) >= 2
    total_chars = sum(len(c) for c in chunks)
    assert total_chars > 200
