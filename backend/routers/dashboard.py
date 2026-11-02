"""Dashboard aggregation and analytical query routes (in-memory store)."""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from ai_engine import analyze_single_record, detect_anomalies, predict_future_failures
from schemas import AnalysisPendingResponse, DailyTrendsResponse, DashboardSummaryOut
from store import store

router = APIRouter(tags=["Analytical Dashboard Aggregation"])


def _extract_counts(rows, allowed_keys):
    out = {k: 0 for k in allowed_keys}
    for key, count in rows:
        norm = str(key).lower()
        out[norm] = int(count)
    return out


@router.get("/api/dashboard/summary", response_model=DashboardSummaryOut)
@router.get("/api/dashboard/summary/", response_model=DashboardSummaryOut)
def get_dashboard_summary(_store: object = Depends(lambda: store)):
    """
    Consolidated analytical metrics for all dashboard charts.
    Aggregates distributions for Sentiment, Severity, Failure Causes, and Daily Trends.
    """
    records = store.all_records()
    total = len(records)

    sentiment_rows = []
    severity_rows = []
    cause_map: dict[str, int] = {}
    alert_rows = []
    daily_map: dict[str, dict[str, int]] = {}

    for r in records:
        sentiment_rows.append((r["sentiment"], 1))
        severity_rows.append((r["severity"], 1))
        cause = r.get("predicted_cause") or "unknown"
        cause_map[cause] = cause_map.get(cause, 0) + 1
        if str(r["severity"]).lower() in ("high", "critical"):
            alert_rows.append((cause, str(r["severity"]).lower(), 1))
        day = (r.get("service_date") or r.get("created_at") or "")[:10]
        if day:
            daily_map.setdefault(day, {"positive": 0, "neutral": 0, "negative": 0})
            sk = str(r["sentiment"]).lower()
            if sk in daily_map[day]:
                daily_map[day][sk] += 1

    def _group(rows):
        agg: dict = {}
        for k, v in rows:
            agg[str(k).lower()] = agg.get(str(k).lower(), 0) + v
        return sorted(agg.items())

    causes = [{"cause": c, "count": cnt} for c, cnt in sorted(cause_map.items(), key=lambda kv: kv[1], reverse=True)]

    alerts_agg: dict = {}
    for c, s, _ in alert_rows:
        key = (c, s)
        alerts_agg[key] = alerts_agg.get(key, 0) + 1
    alerts = [{"cause": c, "severity": s, "count": cnt}
              for (c, s), cnt in sorted(alerts_agg.items(), key=lambda kv: kv[1], reverse=True)]

    daily_list = [
        {"date": day_str, **counts}
        for day_str, counts in sorted(daily_map.items())[-14:]
    ]

    return DashboardSummaryOut(
        total_feedback=total,
        analyzed_feedback=total,
        pending_analysis=0,
        sentiment=_extract_counts(_group(sentiment_rows), ("positive", "neutral", "negative")),
        severity=_extract_counts(_group(severity_rows), ("low", "medium", "high", "critical")),
        causes=causes,
        alerts=alerts,
        daily=daily_list,
    )


@router.get("/api/dashboard/daily-trends", response_model=DailyTrendsResponse)
def get_daily_trends(_store: object = Depends(lambda: store)):
    """Daily feedback volume line chart endpoint."""
    per_day: dict[str, int] = {}
    for r in store.all_records():
        day = (r.get("service_date") or r.get("created_at") or "")[:10]
        if day:
            per_day[day] = per_day.get(day, 0) + 1
    items = [{"date": d, "feedback_count": c} for d, c in sorted(per_day.items())][-30:]
    return DailyTrendsResponse(items=items)


@router.get("/api/feedback")
@router.get("/api/feedback/")
def list_feedback(
    search: str = Query(default="", max_length=300),
    filename: Optional[str] = Query(default=None),
    batch_id: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    sentiment: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _store: object = Depends(lambda: store),
):
    """Search and paginate individual customer feedback records with filters."""
    records = store.all_records()
    records.reverse()  # newest first

    search_val = search.default if hasattr(search, "default") else search
    filename_val = filename.default if hasattr(filename, "default") else filename
    batch_val = batch_id.default if hasattr(batch_id, "default") else batch_id
    severity_val = severity.default if hasattr(severity, "default") else severity
    sentiment_val = sentiment.default if hasattr(sentiment, "default") else sentiment

    if search_val.strip():
        pattern = search_val.strip().lower()
        records = [r for r in records if pattern in r["feedback_text"].lower()]
    if filename_val and str(filename_val).strip():
        records = [r for r in records if r["filename"] == str(filename_val).strip()]
    if batch_val and str(batch_val).strip():
        records = [r for r in records if r.get("batch_id") == str(batch_val).strip()]
    if severity_val and str(severity_val).strip():
        records = [r for r in records if str(r["severity"]).lower() == str(severity_val).strip().lower()]
    if sentiment_val and str(sentiment_val).strip():
        records = [r for r in records if str(r["sentiment"]).lower() == str(sentiment_val).strip().lower()]

    total = len(records)
    items = records[offset:offset + limit]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/api/predictions")
@router.get("/api/predictions/")
def get_predictions(_store: object = Depends(lambda: store)):
    """Predicted failure likelihood for the next 7 days — future-facing, not just historical counts."""
    per_day: dict[str, int] = {}
    cause_counts: dict[str, int] = {}
    for r in store.all_records():
        day = (r.get("service_date") or r.get("created_at") or "")[:10]
        if day:
            per_day[day] = per_day.get(day, 0) + 1
        cause = r.get("predicted_cause") or "unknown"
        cause_counts[cause] = cause_counts.get(cause, 0) + 1

    forecasts = predict_future_failures(sorted(per_day.items()), cause_counts)
    return {"items": forecasts["cause_forecasts"], "forecast": forecasts}


@router.get("/api/alerts")
@router.get("/api/alerts/")
def get_alerts(_store: object = Depends(lambda: store)):
    """High/critical severity alerts PLUS statistical anomaly spikes for Early Warnings."""
    alerts_agg: dict = {}
    per_day: dict[str, int] = {}
    for r in store.all_records():
        if str(r["severity"]).lower() in ("high", "critical"):
            cause = r.get("predicted_cause") or "unknown"
            sev = str(r["severity"]).lower()
            key = (cause, sev)
            alerts_agg[key] = alerts_agg.get(key, 0) + 1
        day = (r.get("service_date") or r.get("created_at") or "")[:10]
        if day:
            per_day[day] = per_day.get(day, 0) + 1

    anomalies = detect_anomalies(sorted(per_day.items()))
    items = [{"cause": c, "severity": s, "count": cnt}
             for (c, s), cnt in sorted(alerts_agg.items(), key=lambda kv: kv[1], reverse=True)]
    return {"items": items, "anomalies": anomalies}
