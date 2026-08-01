from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), nullable=False, unique=True, index=True)
    task_type = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    result_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=False), nullable=True)

    def __repr__(self):
        return f"<TaskRecord id={self.id} task_id={self.task_id} type={self.task_type} status={self.status}>"
