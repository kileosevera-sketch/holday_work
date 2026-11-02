"""Lightweight thread-safe in-memory analysis store.

Replaces the previous SQLAlchemy/SQLite persistence layer. All feedback records
and batch reports now live in process memory — zero setup, zero DB files.

NOTE: data resets when the backend process restarts. Upload your CSV again to
repopulate the dashboard (a sample CSV ships with the project).
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class DataStore:
    """Thread-safe singleton-style in-memory store for feedback records & batches."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: List[Dict[str, Any]] = []   # analyzed feedback items
        self._reports: List[Dict[str, Any]] = []   # batch report metadata
        self._next_id = 1

    # ---- helpers -----------------------------------------------------------
    def _bump_id(self) -> int:
        iid = self._next_id
        self._next_id += 1
        return iid

    # ---- writes ------------------------------------------------------------
    def add_batch(
        self,
        batch_id: str,
        filename: str,
        items: List[Dict[str, Any]],
        duplicates: int,
        invalid_rows: int,
        invalid_dates: int,
        summary: Dict[str, Any],
        trend_metrics: List[Dict[str, Any]],
        root_cause_ranking: List[Dict[str, Any]],
        forecasts: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a batch of analyzed items plus report metadata. Returns report dict."""
        now = datetime.now(timezone.utc)
        with self._lock:
            report_id = self._bump_id()
            critical = sum(1 for it in items if it.get("severity") == "critical")
            report = {
                "id": report_id,
                "batch_id": batch_id,
                "filename": filename,
                "file_type": "xlsx" if filename.lower().endswith((".xlsx", ".xls")) else "csv",
                "file_hash": "",
                "total_feedback_count": len(items),
                "analyzed_feedback_count": len(items),
                "critical_count": critical,
                "duplicate_records_skipped": duplicates,
                "invalid_rows_skipped": invalid_rows,
                "invalid_dates": invalid_dates,
                "summary_metrics": summary,
                "trend_metrics": trend_metrics,
                "root_cause_ranking": root_cause_ranking,
                "future_forecasts": forecasts or {},
                "status": "completed",
                "uploaded_at": now.isoformat(),
            }
            self._reports.append(report)

            for item in items:
                record = dict(item)
                record_id = self._bump_id()
                record["id"] = record_id
                record["report_id"] = report_id
                record["created_at"] = now.isoformat()
                record["status"] = "analyzed"
                self._records.append(record)

            return report

    # ---- reads -------------------------------------------------------------
    def find_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for r in self._reports:
                if r["batch_id"] == batch_id:
                    return r
        return None

    def all_records(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._records)

    def all_reports(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._reports)

    def total_records(self) -> int:
        with self._lock:
            return len(self._records)

    def batch_records(self, report_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            return [r for r in self._records if r.get("report_id") == report_id]


# Module-level shared instance (import this everywhere)
store = DataStore()
