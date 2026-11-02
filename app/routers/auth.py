"""
Authentication Router (/api/v1/auth).

Endpoints:
- POST /signup : Register a new user (farmer, officer, etc.)
- POST /login  : Authenticate credentials and issue JWT bearer token
- GET  /me     : Return profile details of currently authenticated user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models, schemas, security
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user account after validating email format and password strength."
)
def signup(user_data: schemas.UserSignupRequest, db: Session = Depends(get_db)):
    # 1. Check if an account already exists with the given email
    existing_user = db.query(models.User).filter(models.User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in or use a different email."
        )

    # 2. Hash the user's password securely with bcrypt
    hashed_pwd = security.hash_password(user_data.password)

    # 3. Create the database record
    new_user = models.User(
        full_name=user_data.full_name.strip(),
        email=user_data.email.lower().strip(),
        phone=user_data.phone.strip() if user_data.phone else None,
        hashed_password=hashed_pwd,
        language=user_data.language or "en",
        role="farmer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    summary="Log in and retrieve JWT token",
    description="Authenticates credentials and returns a JWT access token with user details."
)
def login(credentials: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    # 1. Locate user by email
    user = db.query(models.User).filter(models.User.email == credentials.email.lower().strip()).first()
    
    # 2. Verify password with bcrypt (generic error message prevents user enumeration)
    if not user or not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate JWT access token with user.id in the 'sub' claim
    token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=token_expires
    )

    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=schemas.UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user profile",
    description="Returns the profile information of the currently authenticated user."
)
def get_profile(current_user: models.User = Depends(security.get_current_user)):
    return current_user

