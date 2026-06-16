"""
User business logic service.
"""

from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.schemas import UserUpdate
from app.core.security import get_password_hash
from fastapi import HTTPException, status


class UserService:
    """Service for user operations."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        user = UserService.get_user_by_id(db, user_id)

        # Check if new email is already taken
        if user_data.email and user_data.email != user.email:
            existing = db.query(User).filter(
                User.email == user_data.email
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)

        # Hash password if updating
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> User:
        """Deactivate user account."""
        user = UserService.get_user_by_id(db, user_id)
        user.is_active = False

        db.commit()
        db.refresh(user)

        return user
