"""CSV upload and feedback analysis route."""
from io import BytesIO
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from ai_engine import analyze_feedback
from crud import insert_analyzed_records
from database import get_db

router = APIRouter(tags=["feedback"])
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

@router.post("/api/upload-and-analyze/")
async def upload_and_analyze(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = Path(file.filename or "feedback.csv").name
    if Path(filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=415, detail="Only CSV files are supported.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV exceeds the 20 MiB upload limit.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")
    try:
        frame = pd.read_csv(BytesIO(content), encoding="utf-8-sig", on_bad_lines="error")
        analyzed = analyze_feedback(frame)
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        saved = insert_analyzed_records(db, analyzed, filename)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Could not save analysis to the database.") from exc
    return {
        "filename": filename,
        "total_rows": int(len(frame)),
        "analyzed_rows": int(len(analyzed)),
        "saved_rows": saved,
        "sentiment_counts": {str(k): int(v) for k, v in analyzed["sentiment"].value_counts().items()},
        "severity_counts": {str(k): int(v) for k, v in analyzed["severity"].value_counts().items()},
        "records": analyzed[["feedback_text", "sentiment", "severity", "predicted_cause"]].to_dict(orient="records"),
    }
