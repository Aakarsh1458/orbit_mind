import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=True)
    analysis_type = Column(String(50), nullable=False)
    imagery_ids = Column(JSON, nullable=False)  # list of imagery UUIDs
    status = Column(String(20), nullable=False, default="queued")  # queued, processing, completed, failed
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 1-to-1 relationship with result
    result = relationship("AnalysisResult", back_populates="job", uselist=False, cascade="all, delete-orphan")

    @property
    def job_id(self) -> str:
        return self.id

    def __repr__(self):
        return f"<AnalysisJob id={self.id} type={self.analysis_type} status={self.status} progress={self.progress}>"
