"""End-to-End integration test suite for the FastAPI backend and AI pipelines."""
import sys
import os
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

os.environ["APP_USERNAME"] = "test-admin"
os.environ["APP_PASSWORD"] = "test-password"
os.environ["APP_AUTH_SECRET"] = "test-signing-secret-that-is-at-least-32-chars"

from fastapi.testclient import TestClient
from main import app

def run_tests():
    client = TestClient(app)

    print("1. Testing GET /health...")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print("   -> OK:", resp.json()["status"])

    print("2. Testing login and protected API access...")
    assert client.get("/api/dashboard/summary").status_code == 401
    login = client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    print("   -> Login successful; unauthenticated API access is blocked.")

    print("3. Testing POST /api/upload with sample CSV...")
    csv_path = backend_dir / "sample_postsale_feedback.csv"
    assert csv_path.exists(), f"Sample CSV missing at {csv_path}"

    with open(csv_path, "rb") as f:
        resp = client.post("/api/upload", files={"file": ("sample.csv", f, "text/csv")})
    assert resp.status_code == 200, f"Upload failed: {resp.text}"
    data = resp.json()
    batch_id = data["batch_id"]
    print(f"   -> OK: Uploaded {data['new_records_uploaded']} records. Batch ID: {batch_id}")

    print("4. Testing GET /api/dashboard/summary...")
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200, f"Summary failed: {resp.text}"
    summary = resp.json()
    print("   -> Total records:", summary["total_feedback"])
    print("   -> Sentiment distribution:", summary["sentiment"])
    print("   -> Severity distribution:", summary["severity"])
    print("   -> Top failure causes:", len(summary["causes"]))
    print("   -> Alerts count:", len(summary["alerts"]))

    print("5. Testing GET /api/alerts (anomaly detection)...")
    resp = client.get("/api/alerts")
    assert resp.status_code == 200, f"Alerts failed: {resp.text}"
    alerts = resp.json()
    print("   -> Severity-based alerts:", len(alerts["items"]))
    print("   -> Statistical anomalies:", len(alerts["anomalies"]))
    for a in alerts["anomalies"][:3]:
        print(f"      * {a['date']}: z={a['z_score']} severity={a['severity']}")

    print("6. Testing GET /api/predictions (future failure likelihood)...")
    resp = client.get("/api/predictions")
    assert resp.status_code == 200, f"Predictions failed: {resp.text}"
    preds = resp.json()
    fc = preds["forecast"]
    print(f"   -> Horizon: {fc['horizon_days']} days, forecast total: {fc['forecast_total_failures']}")
    for c in fc["cause_forecasts"][:3]:
        print(f"      * {c['cause']}: {c['likelihood_pct']}% likelihood, trend={c['trend']}")

    print("7. Testing GET /api/dashboard/daily-trends...")
    resp = client.get("/api/dashboard/daily-trends")
    assert resp.status_code == 200, f"Daily trends failed: {resp.text}"
    trends = resp.json()
    print("   -> Trend items:", len(trends["items"]))

    print("8. Testing GET /api/reports...")
    resp = client.get("/api/reports")
    assert resp.status_code == 200, f"List reports failed: {resp.text}"
    reports = resp.json()
    assert len(reports["items"]) > 0, "No reports returned"
    report_id = reports["items"][0]["id"]
    print(f"   -> OK: Found {len(reports['items'])} reports. First report ID: {report_id}")

    print(f"9. Testing GET /api/reports/{report_id}...")
    resp = client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200, f"Report detail failed: {resp.text}"
    detail = resp.json()
    print("   -> Root cause rankings in report:", len(detail.get("root_cause_ranking", [])))

    print("10. Testing GET /api/feedback search...")
    resp = client.get("/api/feedback?limit=10")
    assert resp.status_code == 200, f"Feedback query failed: {resp.text}"
    feedbacks = resp.json()
    print(f"   -> OK: Retrieved {len(feedbacks['items'])} feedback records out of {feedbacks['total']}")

    print("11. Testing GET /api/reports/feedback.csv...")
    resp = client.get("/api/reports/feedback.csv")
    assert resp.status_code == 200, f"CSV export failed: {resp.text}"
    assert "id,filename,feedback_text" in resp.text
    print("   -> CSV export OK, length:", len(resp.text))

    print("12. Testing complete and batch PDF exports...")
    for path in (
        "/api/reports/analysis-report.pdf",
        f"/api/reports/analysis-report.pdf?batch_id={data['batch_id']}",
    ):
        pdf = client.get(path)
        assert pdf.status_code == 200, f"PDF export failed: {pdf.text[:300]}"
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.content.startswith(b"%PDF-")
    print("   -> Both PDF exports contain valid PDF documents.")

    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
