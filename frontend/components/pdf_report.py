from backend.reports.pdf_report import ReportGenerator
from backend.database.db import Database


def generate_user_report(session_id: int, output_dir: str = "data/reports") -> str:
    db = Database()
    generator = ReportGenerator()
    return generator.generate_session_report(session_id, db, output_path=None)
