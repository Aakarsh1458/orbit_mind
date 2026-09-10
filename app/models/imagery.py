import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean
from app.models.database import Base


class Imagery(Base):
    __tablename__ = "imagery"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    sensor = Column(String(100), default="Unknown")
    acquisition_time = Column(DateTime, nullable=True)
    crs = Column(String(100), nullable=False, default="EPSG:4326")
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    bands = Column(Integer, nullable=False, default=1)
    bounds = Column(JSON, nullable=False)  # {"left": ..., "bottom": ..., "right": ..., "top": ...}
    resolution = Column(JSON, nullable=False)  # [res_x, res_y]
    dtype = Column(String(50), nullable=False, default="uint8")
    is_georeferenced = Column(Boolean, default=True)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    meta_info = Column(JSON, nullable=True)  # tags, transform, driver
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Imagery id={self.id} filename={self.filename} dimensions={self.width}x{self.height}>"
