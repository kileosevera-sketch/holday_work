"""Pydantic schemas for data validation and standardized API serialization."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DashboardSummaryOut(BaseModel):
    total_feedback: int
    analyzed_feedback: int
    pending_analysis: int
    sentiment: Dict[str, int]
    severity: Dict[str, int]
    causes: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    daily: List[Dict[str, Any]]


class DailyTrendItem(BaseModel):
    date: str
    feedback_count: int


class DailyTrendsResponse(BaseModel):
    items: List[DailyTrendItem]


class UploadResponse(BaseModel):
    message: str
    batch_id: str
    filename: str
    file_feedback_rows: int
    new_records_uploaded: int
    duplicate_records_skipped: int
    invalid_rows_skipped: int
    database_total_records: int
    invalid_dates: int = 0
    records: List[Dict[str, Any]] = Field(default_factory=list)


class AnalysisPendingResponse(BaseModel):
    analyzed: int
    analysis_method: str = "Enterprise NLP & Root-Cause Bayesian Classification"
