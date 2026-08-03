from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(64), nullable=False)  # e.g., 'alert', 'info', 'action_required'
    priority = Column(String(32), nullable=False, default="normal")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Notification id={self.id} patient_id={self.patient_id} title={self.title[:20]}>"
