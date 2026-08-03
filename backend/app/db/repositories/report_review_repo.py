from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.report_review import ReportReview


def create_review(db: Session, review_in: dict) -> ReportReview:
    r = ReportReview(
        report_id=review_in["report_id"],
        doctor_id=review_in["doctor_id"],
        status=review_in.get("status", "pending"),
        comment=review_in.get("comment"),
        stage_review=review_in.get("stage_review"),
        risk_review=review_in.get("risk_review"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_review_by_report(db: Session, report_id: int) -> Optional[ReportReview]:
    return db.query(ReportReview).filter(ReportReview.report_id == report_id).one_or_none()


def get_review(db: Session, review_id: int) -> Optional[ReportReview]:
    return db.query(ReportReview).filter(ReportReview.id == review_id).one_or_none()


def update_review(db: Session, review: ReportReview, updates: dict) -> ReportReview:
    for k, v in updates.items():
        setattr(review, k, v)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def list_reviews(db: Session, limit: int =50, offset: int =0) -> List[ReportReview]:
    return db.query(ReportReview).order_by(ReportReview.created_at.desc()).limit(limit).offset(offset).all()
