"""Database model for analyzed customer feedback."""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class FeedbackAnalysisModel(Base):
    __tablename__ = "feedback_analysis"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    predicted_cause: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
