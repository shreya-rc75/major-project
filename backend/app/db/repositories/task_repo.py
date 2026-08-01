from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.task import TaskRecord


def get_task_by_id(db: Session, id: int) -> Optional[TaskRecord]:
    return db.query(TaskRecord).filter(TaskRecord.id == id).one_or_none()


def get_task_by_taskid(db: Session, task_id: str) -> Optional[TaskRecord]:
    return db.query(TaskRecord).filter(TaskRecord.task_id == task_id).one_or_none()


def create_task(db: Session, task_in: dict) -> TaskRecord:
    task = TaskRecord(**task_in)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: TaskRecord, updates: dict) -> TaskRecord:
    for k, v in updates.items():
        setattr(task, k, v)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: TaskRecord) -> None:
    db.delete(task)
    db.commit()
