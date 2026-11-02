"""
Users Router (/api/v1/users).

Endpoints:
- PATCH /me : Update current user profile fields (name, phone, language)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.patch(
    "/me",
    response_model=schemas.UserResponse,
    summary="Update current user profile",
    description="Updates optional profile fields such as full name, phone number, and preferred language."
)
def update_profile(
    update_data: schemas.UserUpdateRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name.strip()
    if update_data.phone is not None:
        current_user.phone = update_data.phone.strip()
    if update_data.language is not None:
        current_user.language = update_data.language

    db.commit()
    db.refresh(current_user)
    return current_user

