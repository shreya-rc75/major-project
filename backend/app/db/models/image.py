from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    preprocessed = Column(Boolean, nullable=False, default=False)

    study = relationship("Study", back_populates="images")
    analyses = relationship("AnalysisResult", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Image id={self.id} filename={self.filename} study_id={self.study_id}>"
