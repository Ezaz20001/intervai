from backend.ingestion.entities import ResumeEntityExtractor


def test_extract_skills_from_text():
    extractor = ResumeEntityExtractor()
    text = (
        "SKILLS: Python, JavaScript, Docker, Kubernetes, React\n"
        "Proficient in AWS and PostgreSQL"
    )
    entities = extractor.extract(text)
    assert "skills" in entities
    assert isinstance(entities["skills"], list)
    assert len(entities["skills"]) > 0
    assert any("Python" in s for s in entities["skills"])


def test_extract_projects_from_text():
    extractor = ResumeEntityExtractor()
    text = (
        "PROJECTS\n"
        "- Built a real-time analytics dashboard using React and WebSocket\n"
        "- Developed an ETL pipeline for processing terabytes of data\n"
    )
    entities = extractor.extract(text)
    assert "projects" in entities
    assert isinstance(entities["projects"], list)
    assert len(entities["projects"]) >= 2


def test_extract_education():
    extractor = ResumeEntityExtractor()
    text = "Bachelor of Science in Computer Science from MIT"
    entities = extractor.extract(text)
    assert "education" in entities
    assert isinstance(entities["education"], list)
    assert len(entities["education"]) >= 1


def test_empty_text():
    extractor = ResumeEntityExtractor()
    entities = extractor.extract("")
    assert entities["skills"] == []
    assert entities["projects"] == []
    assert entities["education"] == []
