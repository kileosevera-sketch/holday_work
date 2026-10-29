"""Persistence operations for feedback analyses."""
from sqlalchemy.orm import Session
from models import FeedbackAnalysisModel

def insert_analyzed_records(db: Session, frame, filename: str) -> int:
    """Insert every analyzed DataFrame row in a single transaction."""
    required = ("feedback_text", "sentiment", "severity", "predicted_cause")
    missing = set(required).difference(frame.columns)
    if missing:
        raise ValueError(f"Analyzed data is missing columns: {', '.join(sorted(missing))}")
    count = 0
    try:
        for row in frame.loc[:, list(required)].to_dict(orient="records"):
            db.add(FeedbackAnalysisModel(filename=filename[:255], feedback_text=str(row["feedback_text"]),
                sentiment=str(row["sentiment"]), severity=str(row["severity"]), predicted_cause=str(row["predicted_cause"])))
            count += 1
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
