"""
User profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import UserResponse, UserUpdate
from app.models.models import User
from app.services.user_service import UserService
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Update current user profile."""
    updated_user = UserService.update_user(db, current_user.id, user_data)
    return updated_user


@router.post("/me/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Deactivate current user account."""
    UserService.deactivate_user(db, current_user.id)
    return {"message": "Account deactivated. Please remove token from client."}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_public(
    user_id: int,
    db: Session = Depends(get_db)
) -> User:
    """Get public user information (username only for now)."""
    user = UserService.get_user_by_id(db, user_id)
    return user
