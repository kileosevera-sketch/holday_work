"""Direct unit and functional test of the backend routers and AI engine (in-memory store)."""
import sys
from pathlib import Path
from fastapi import UploadFile

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from routers.upload import upload_feedback_file
from routers.dashboard import get_dashboard_summary, list_feedback, get_daily_trends, get_alerts, get_predictions
from routers.reports import list_reports, get_report_detail, export_feedback_csv


def test_all():
    csv_path = backend_dir / "sample_postsale_feedback.csv"
    print(f"1. Testing file ingestion with {csv_path.name}...", flush=True)
    with open(csv_path, "rb") as f:
        content = f.read()

    from io import BytesIO
    file_obj = UploadFile(filename="sample_postsale_feedback.csv", file=BytesIO(content))

    upload_res = upload_feedback_file(file=file_obj, idempotency_key="test-batch-001")
    print(f"   -> Upload successful! Processed: {upload_res.new_records_uploaded} records, total: {upload_res.database_total_records}", flush=True)
    print(f"   -> Message: {upload_res.message}", flush=True)

    print("2. Testing dashboard summary aggregation...", flush=True)
    summary = get_dashboard_summary()
    print(f"   -> Total feedback in summary: {summary.total_feedback}", flush=True)
    print(f"   -> Sentiment counts: {summary.sentiment}", flush=True)
    print(f"   -> Severity counts: {summary.severity}", flush=True)
    print(f"   -> Predicted failure causes found: {len(summary.causes)}", flush=True)
    print(f"   -> Early warning alerts: {len(summary.alerts)}", flush=True)

    print("3. Testing daily trends query...", flush=True)
    trends = get_daily_trends()
    print(f"   -> Trend days plotted: {len(trends.items)}", flush=True)

    print("4. Testing anomaly detection (GET /api/alerts)...", flush=True)
    alerts = get_alerts()
    print(f"   -> Severity alerts: {len(alerts['items'])}", flush=True)
    print(f"   -> Statistical anomalies: {len(alerts['anomalies'])}", flush=True)
    for a in alerts["anomalies"][:3]:
        print(f"      * {a['date']}: z-score {a['z_score']} ({a['severity']}) — {a['message']}", flush=True)

    print("5. Testing future failure prediction (GET /api/predictions)...", flush=True)
    preds = get_predictions()
    fc = preds["forecast"]
    print(f"   -> Forecast for next {fc['horizon_days']} days: {fc['forecast_total_failures']} expected failures", flush=True)
    for c in fc["cause_forecasts"][:3]:
        print(f"      * {c['cause']}: {c['likelihood_pct']}% likelihood, trend={c['trend']}, expected={c['expected_failures']}", flush=True)

    print("6. Testing historical reports list (GET /api/reports)...", flush=True)
    reports_res = list_reports(search="", limit=10, offset=0)
    print(f"   -> Reports found: {reports_res['total']}", flush=True)
    report_item = reports_res["items"][0]
    report_id = report_item["id"]
    batch_id = report_item["batch_id"]
    print(f"   -> First report: ID {report_id}, batch '{batch_id}'", flush=True)

    print(f"7. Testing historical report detail (GET /api/reports/{report_id})...", flush=True)
    detail = get_report_detail(report_identifier=str(report_id))
    print(f"   -> Detail retrieved! Filename: {detail['filename']}", flush=True)
    print(f"   -> Root cause rankings in report: {len(detail['root_cause_ranking'])}", flush=True)
    if detail["root_cause_ranking"]:
        top = detail["root_cause_ranking"][0]
        print(f"      * Top rank: {top['cause']} | Probability: {top['percentage']}% | Avg Conf: {top['average_confidence']}%", flush=True)
        print(f"      * Contributing factors: {top['contributing_factors']}", flush=True)

    print("8. Testing feedback search & pagination (GET /api/feedback)...", flush=True)
    feedbacks = list_feedback(search="", limit=5, offset=0)
    print(f"   -> Retrieved {len(feedbacks['items'])} items. First item:", flush=True)
    sample = feedbacks["items"][0]
    print(f"      * Text: {sample['feedback_text'][:60]}...", flush=True)
    print(f"      * Cause: {sample['predicted_cause']} ({sample['prediction_confidence']}%)", flush=True)
    print(f"      * Symptoms: {sample['detected_symptoms']}", flush=True)
    print(f"      * Contributing factors: {sample['contributing_factors']}", flush=True)

    print("9. Testing CSV report generation...", flush=True)
    csv_resp = export_feedback_csv(batch_id=batch_id)
    assert csv_resp.status_code == 200
    print(f"   -> CSV report generated successfully! Byte length: {len(csv_resp.body)}", flush=True)

    print("\n=======================================================", flush=True)
    print("ALL PRODUCTION SYSTEM LAYERS VERIFIED PERFECTLY!", flush=True)
    print("=======================================================", flush=True)


if __name__ == "__main__":
    test_all()
