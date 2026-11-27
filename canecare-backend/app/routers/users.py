"""
Users Router (/api/v1/users).

Endpoints:
- PATCH /me : Update current user profile fields (name, phone, language, and farm profile)
- GET /me   : Get current user profile with farm details
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user profile",
    description="Returns the full profile and farming details of the authenticated user."
)
def get_my_profile(current_user: models.User = Depends(security.get_current_user)):
    return current_user


@router.patch(
    "/me",
    response_model=schemas.UserResponse,
    summary="Update current user profile",
    description="Updates optional profile fields such as full name, phone number, language, and farm details."
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
    if update_data.region is not None:
        current_user.region = update_data.region.strip()
    if update_data.village is not None:
        current_user.village = update_data.village.strip()
    if update_data.avatar_path is not None:
        current_user.avatar_path = update_data.avatar_path.strip()
    if update_data.farm_size is not None:
        current_user.farm_size = update_data.farm_size.strip()
    if update_data.sugarcane_variety is not None:
        current_user.sugarcane_variety = update_data.sugarcane_variety.strip()
    if update_data.irrigation_type is not None:
        current_user.irrigation_type = update_data.irrigation_type.strip()
    if update_data.planting_season is not None:
        current_user.planting_season = update_data.planting_season.strip()

    db.commit()
    db.refresh(current_user)
    return current_user
