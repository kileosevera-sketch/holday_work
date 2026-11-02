"""File upload, streaming ingestion pipeline, and batch analysis router (in-memory store)."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
from pathlib import Path
import uuid
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ai_engine import (
    analyze_dataframe,
    clean_text,
    detect_anomalies,
    predict_future_failures,
)
from schemas import UploadResponse
from store import store

router = APIRouter(tags=["Upload & Ingestion Pipeline"])

MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MiB safety boundary


def _parse_file_to_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    """Safely stream and parse uploaded CSV or Excel binary content into a pandas DataFrame."""
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                return pd.read_csv(BytesIO(content), encoding=encoding, on_bad_lines="skip")
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to decode CSV file with standard UTF-8 or Latin-1 encodings.",
        )
    elif ext in (".xlsx", ".xls"):
        try:
            return pd.read_excel(BytesIO(content))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse Excel spreadsheet: {exc}",
            ) from exc
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx) file.",
        )


def _detect_date_column(df: pd.DataFrame) -> str | None:
    lookup = {str(col).strip().lower(): col for col in df.columns}
    for cand in ("date", "service_date", "feedback_date", "created_at", "timestamp", "datetime"):
        if cand in lookup:
            return lookup[cand]
    return None


@router.post("/api/upload", response_model=UploadResponse)
@router.post("/api/feedback/upload", response_model=UploadResponse)
@router.post("/api/upload-and-analyze/", response_model=UploadResponse)
def upload_feedback_file(
    file: UploadFile = File(...),
    idempotency_key: str | None = Form(default=None),
    _store: object = Depends(lambda: store),
):
    """
    Ingest, validate, and analyze customer feedback from CSV or Excel files.
    Extracts text, identifies symptoms, predicts root causes, runs anomaly detection,
    forecasts future failure likelihood, and stores everything in the in-memory archive.
    """
    filename = Path(file.filename or "uploaded_feedback.csv").name
    ext = Path(filename).suffix.lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported format. Only CSV (.csv) and Excel (.xlsx) files are supported.",
        )

    content = file.file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum 25 MiB limit.",
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please provide a file with feedback data.",
        )

    file_hash = hashlib.sha256(content).hexdigest()
    batch_id = idempotency_key.strip() if idempotency_key and idempotency_key.strip() else f"batch-{uuid.uuid4().hex[:12]}"

    # Idempotency Check: Return existing report if batch_id already exists
    existing_report = store.find_batch(batch_id)
    if existing_report:
        existing_items = store.batch_records(existing_report["id"])[:15]
        return UploadResponse(
            message=f"Batch '{batch_id}' has already been processed (Idempotent response).",
            batch_id=batch_id,
            filename=existing_report["filename"],
            file_feedback_rows=existing_report["total_feedback_count"],
            new_records_uploaded=0,
            duplicate_records_skipped=existing_report["total_feedback_count"],
            invalid_rows_skipped=existing_report["invalid_rows_skipped"],
            database_total_records=store.total_records(),
            invalid_dates=existing_report.get("invalid_dates", 0),
            records=existing_items,
        )

    df = _parse_file_to_dataframe(filename, content)
    total_raw_rows = len(df)
    if total_raw_rows == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file contains headers but no data records.",
        )

    date_col = _detect_date_column(df)
    parsed_dates = []
    invalid_dates_count = 0
    now_utc = datetime.now(timezone.utc)

    if date_col:
        for val in df[date_col]:
            try:
                dt = pd.to_datetime(val, errors="coerce")
                if pd.isna(dt):
                    parsed_dates.append(now_utc)
                    invalid_dates_count += 1
                else:
                    parsed_dates.append(dt.to_pydatetime())
            except Exception:
                parsed_dates.append(now_utc)
                invalid_dates_count += 1
    else:
        parsed_dates = [now_utc] * total_raw_rows

    df["__service_date"] = parsed_dates

    # Run Enterprise NLP & Failure Prediction Engine
    try:
        analyzed_df, analytics = analyze_dataframe(df)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err

    # De-duplicate against existing records already in the in-memory archive
    existing_texts = {r["feedback_text"] for r in store.all_records()}

    new_items: list[dict] = []
    duplicates_count = 0
    invalid_rows_count = total_raw_rows - len(analyzed_df)

    daily_counter: dict[str, dict[str, int]] = {}

    for _, row in analyzed_df.iterrows():
        text = row["feedback_text"]
        if text in existing_texts:
            duplicates_count += 1
            continue

        s_date = row["__service_date"]
        date_str = s_date.strftime("%Y-%m-%d") if isinstance(s_date, datetime) else now_utc.strftime("%Y-%m-%d")
        daily_counter.setdefault(date_str, {"feedback_count": 0, "positive": 0, "neutral": 0, "negative": 0})
        daily_counter[date_str]["feedback_count"] += 1
        daily_counter[date_str][row["sentiment"]] += 1

        new_items.append({
            "batch_id": batch_id,
            "filename": filename,
            "feedback_text": text,
            "cleaned_text": clean_text(text),
            "service_date": s_date.isoformat() if isinstance(s_date, datetime) else None,
            "sentiment": row["sentiment"],
            "sentiment_score": row["sentiment_score"],
            "severity": row["severity"],
            "severity_priority": row["severity_priority"],
            "detected_symptoms": list(row["detected_symptoms"]),
            "predicted_cause": row["predicted_cause"],
            "prediction_confidence": row["prediction_confidence"],
            "contributing_factors": list(row["contributing_factors"]),
        })

    # Daily trend metrics for this batch
    trend_metrics = [
        {"date": d, "feedback_count": vals["feedback_count"], "positive": vals["positive"], "neutral": vals["neutral"], "negative": vals["negative"]}
        for d, vals in sorted(daily_counter.items())
    ]

    # ---- NEW: Statistical anomaly detection (early warnings) ---------------
    global_daily = {}
    for r in store.all_records():
        d = (r.get("service_date") or r.get("created_at", ""))[:10]
        global_daily[d] = global_daily.get(d, 0) + 1
    for d, vals in daily_counter.items():
        global_daily[d] = global_daily.get(d, 0) + vals["feedback_count"]
    global_daily = dict(sorted(global_daily.items()))
    anomalies = detect_anomalies(list(global_daily.items()))

    # ---- NEW: Forward-looking failure prediction ----------------------------
    cause_counts = {r["predicted_cause"]: 0 for r in new_items}
    for r in store.all_records() + new_items:
        cause_counts[r["predicted_cause"]] = cause_counts.get(r["predicted_cause"], 0) + 1
    forecasts = predict_future_failures(list(global_daily.items()), cause_counts)

    # Persist batch + items into the in-memory store
    report = store.add_batch(
        batch_id=batch_id,
        filename=filename,
        items=new_items,
        duplicates=duplicates_count,
        invalid_rows=invalid_rows_count,
        invalid_dates=invalid_dates_count,
        summary=analytics["summary"],
        trend_metrics=trend_metrics,
        root_cause_ranking=analytics["root_cause_ranking"],
        forecasts={"anomalies": anomalies, "prediction": forecasts},
    )

    total_in_store = store.total_records()

    preview_records = [
        {
            "id": it["id"],
            "feedback_text": it["feedback_text"],
            "sentiment": it["sentiment"],
            "severity": it["severity"],
            "predicted_cause": it["predicted_cause"],
            "prediction_confidence": it["prediction_confidence"],
            "created_at": it["created_at"],
        }
        for it in store.batch_records(report["id"])[:15]
    ]

    return UploadResponse(
        message=(
            f"Successfully processed {len(new_items)} new feedback records from {filename}. "
            f"{len(anomalies)} anomaly warning(s) detected; predicted "
            f"{forecasts['forecast_total_failures']} failures over the next {forecasts['horizon_days']} days."
        ),
        batch_id=batch_id,
        filename=filename,
        file_feedback_rows=len(analyzed_df),
        new_records_uploaded=len(new_items),
        duplicate_records_skipped=duplicates_count,
        invalid_rows_skipped=invalid_rows_count,
        database_total_records=int(total_in_store),
        invalid_dates=invalid_dates_count,
        records=preview_records,
    )
