import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    mode = Column(String(20), nullable=False, default="mock")  # mock or production
    statistics = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    execution_trace = Column(JSON, nullable=False)
    result_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("AnalysisJob", back_populates="result")

    def __repr__(self):
        return f"<AnalysisResult id={self.id} job_id={self.job_id} confidence={self.confidence}>"
