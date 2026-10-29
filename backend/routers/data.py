"""Read and export analyzed feedback for dashboard pages."""
import csv
from io import StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from database import get_db
from models import FeedbackAnalysisModel as Feedback

router = APIRouter(prefix="/api", tags=["feedback data"])


def _counts(rows, field):
    result = {key: 0 for key in field}
    for value, count in rows:
        key = str(value).lower()
        result[key] = result.get(key, 0) + int(count)
    return result


@router.get("/feedback/")
def list_feedback(
    search: str = Query(default="", max_length=300),
    filename: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Feedback)
    filters = []
    if search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(Feedback.feedback_text.ilike(pattern))
    if filename:
        filters.append(Feedback.filename == filename)
    if filters:
        from sqlalchemy import and_
        query = query.where(and_(*filters))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(Feedback.created_at.desc(), Feedback.id.desc()).offset(offset).limit(limit)).all()
    return {
        "items": [{
            "id": row.id,
            "filename": row.filename,
            "feedback_text": row.feedback_text,
            "sentiment": row.sentiment,
            "severity": row.severity,
            "predicted_cause": row.predicted_cause,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        } for row in rows],
        "total": int(total), "limit": limit, "offset": offset,
    }


@router.get("/dashboard/summary/")
def dashboard_summary(db: Session = Depends(get_db)):
    total = int(db.scalar(select(func.count(Feedback.id))) or 0)
    sentiment_rows = db.execute(select(Feedback.sentiment, func.count(Feedback.id)).group_by(Feedback.sentiment)).all()
    severity_rows = db.execute(select(Feedback.severity, func.count(Feedback.id)).group_by(Feedback.severity)).all()
    cause_rows = db.execute(select(Feedback.predicted_cause, func.count(Feedback.id)).group_by(Feedback.predicted_cause).order_by(func.count(Feedback.id).desc())).all()
    by_day = db.execute(
        select(func.date(Feedback.created_at), Feedback.sentiment, func.count(Feedback.id))
        .group_by(func.date(Feedback.created_at), Feedback.sentiment)
        .order_by(func.date(Feedback.created_at))
    ).all()
    daily = {}
    for date, sentiment, count in by_day:
        day = str(date)
        key = str(sentiment).lower()
        daily.setdefault(day, {"positive": 0, "neutral": 0, "negative": 0})[key] += int(count)
    return {
        "total_feedback": total,
        "sentiment": _counts(sentiment_rows, ("positive", "neutral", "negative")),
        "severity": _counts(severity_rows, ("low", "medium", "high", "critical")),
        "causes": [{"cause": str(cause), "count": int(count)} for cause, count in cause_rows],
        "daily": [{"date": day, **counts} for day, counts in daily.items()],
    }


@router.get("/predictions/")
def predictions(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Feedback.predicted_cause, func.count(Feedback.id).label("count"))
        .group_by(Feedback.predicted_cause).order_by(func.count(Feedback.id).desc())
    ).all()
    return {"items": [{"cause": str(cause), "count": int(count)} for cause, count in rows]}


@router.get("/alerts/")
def alerts(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Feedback.predicted_cause, func.lower(Feedback.severity).label("severity"), func.count(Feedback.id).label("count"))
        .where(func.lower(Feedback.severity).in_(("high", "critical")))
        .group_by(Feedback.predicted_cause, func.lower(Feedback.severity))
        .order_by(func.count(Feedback.id).desc())
    ).all()
    return {"items": [{"cause": str(cause), "severity": str(severity), "count": int(count)} for cause, severity, count in rows]}


@router.get("/reports/")
def reports(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Feedback.filename,
            func.min(Feedback.created_at).label("created_at"),
            func.count(Feedback.id).label("feedback_count"),
            func.sum(case((func.lower(Feedback.sentiment) == "positive", 1), else_=0)).label("positive"),
            func.sum(case((func.lower(Feedback.sentiment) == "neutral", 1), else_=0)).label("neutral"),
            func.sum(case((func.lower(Feedback.sentiment) == "negative", 1), else_=0)).label("negative"),
            func.sum(case((func.lower(Feedback.severity) == "critical", 1), else_=0)).label("critical"),
        ).group_by(Feedback.filename).order_by(func.max(Feedback.created_at).desc())
    ).all()
    return {"items": [{
        "filename": row.filename,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "feedback_count": int(row.feedback_count or 0),
        "positive": int(row.positive or 0), "neutral": int(row.neutral or 0), "negative": int(row.negative or 0),
        "critical": int(row.critical or 0),
    } for row in rows]}


@router.get("/feedback/export/")
def export_feedback(filename: str | None = Query(default=None, max_length=255), db: Session = Depends(get_db)):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(("id", "filename", "feedback_text", "sentiment", "severity", "predicted_cause", "created_at"))
    query = select(Feedback).order_by(Feedback.created_at.desc(), Feedback.id.desc())
    if filename:
        query = query.where(Feedback.filename == filename)
    rows = db.scalars(query).yield_per(1000)
    for row in rows:
        writer.writerow((row.id, row.filename, row.feedback_text, row.sentiment, row.severity, row.predicted_cause, row.created_at.isoformat() if row.created_at else ""))
    return Response(
        content="\ufeff" + buffer.getvalue(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="feedback-export.csv"'},
    )
