"""
User Management and Clinician Directory API Endpoints
Allows authenticated users to browse recipients for secure image sharing,
and administrators to manage accounts and permissions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.db_models import User
from app.models.schemas import UserProfile
from app.security.rbac import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("", response_model=List[UserProfile])
def list_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Lists active users and their ECDH public keys for sharing."""
    users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "email": u.email,
            "role_name": u.role.role_name if u.role else "USER",
            "public_key_pem": u.public_key_pem,
            "created_at": u.created_at
        }
        for u in users
    ]

@router.get("/{user_id}", response_model=UserProfile)
def get_user_by_id(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role_name": user.role.role_name if user.role else "USER",
        "public_key_pem": user.public_key_pem,
        "created_at": user.created_at
    }

@router.patch("/{user_id}/toggle-status")
def toggle_user_status(user_id: str, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    """Admin-only: Deactivate or activate a user account."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.user_id == admin_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot alter your own administrative status")
    
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User status updated to {'Active' if user.is_active else 'Deactivated'}", "is_active": user.is_active}
