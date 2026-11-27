"""
Prediction & App Feedback Router (/api/v1/feedback).

Enables:
1. Ground-truth corrections on disease predictions (POST /api/v1/feedback)
2. General app feedback, bug reports & translation suggestions (POST /api/v1/feedback/app)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])


@router.post(
    "",
    response_model=schemas.FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on a prediction",
    description="Allows users to indicate whether the model's diagnosis was correct and optionally provide the true disease."
)
def submit_prediction_feedback(
    feedback_data: schemas.FeedbackCreateRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify the scan exists and belongs to current user
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == feedback_data.scan_id, models.Scan.user_id == current_user.id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found or does not belong to your account."
        )

    # Create feedback entry
    feedback_entry = models.Feedback(
        scan_id=feedback_data.scan_id,
        is_correct=feedback_data.is_correct,
        true_class=feedback_data.true_class.strip().lower() if feedback_data.true_class else None,
        comment=feedback_data.comment.strip() if feedback_data.comment else None
    )

    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    return feedback_entry


@router.post(
    "/app",
    response_model=schemas.AppFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit general app feedback or bug report",
    description="Allows farmers to submit app feedback, translation corrections, or feature suggestions."
)
def submit_app_feedback(
    feedback_data: schemas.AppFeedbackRequest,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db)
):
    app_feedback = models.AppFeedback(
        user_id=current_user.id if current_user else None,
        name=feedback_data.name.strip(),
        email=feedback_data.email.strip().lower(),
        feedback_type=feedback_data.feedback_type.strip(),
        message=feedback_data.message.strip()
    )
    db.add(app_feedback)
    db.commit()
    db.refresh(app_feedback)

    return app_feedback
