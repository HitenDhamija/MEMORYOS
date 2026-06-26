"""
User profile endpoints.
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import UserResponse, UserUpdate
from app.models.models import User
from app.services.user_service import UserService
from app.api.deps import get_current_user
from app.core.config import settings

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


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Upload profile picture."""
    allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, and WebP images are allowed")
    
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 5MB")
    
    ext = file.filename.split('.')[-1].lower() if file.filename else 'jpg'
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    avatar_dir = os.path.join(settings.upload_dir, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    file_path = os.path.join(avatar_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


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
