from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from src.config import settings
from src.middlewares.error_handler import AppError
from src.models.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from src.services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    users_db,
    verify_password
)

router = APIRouter(prefix="/users", tags=["Users & Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(user_in: UserCreate):
    """
    Registers a new user account with hashed credentials.
    """
    if user_in.email in users_db:
        raise AppError(
            code="USER_ALREADY_EXISTS",
            message=f"User with email '{user_in.email}' already exists.",
            status_code=status.HTTP_409_CONFLICT
        )

    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "role": user_in.role,
        "hashed_password": hash_password(user_in.password),
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    users_db[user_in.email] = new_user

    return UserResponse(**new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive access token"
)
async def login(credentials: UserLogin):
    """
    Validates user email and password, issuing a signed Bearer JWT.
    """
    user = users_db.get(credentials.email)
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile"
)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Returns the profile information of the currently authenticated caller.
    """
    return current_user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users (Admin only)"
)
async def list_users(_: UserResponse = Depends(require_admin)):
    """
    Admin-only endpoint to enumerate registered users.
    """
    return [UserResponse(**u) for u in users_db.values()]
