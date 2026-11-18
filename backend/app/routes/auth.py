"""
Authentication REST API Endpoints
Handles user registration, login, JWT token generation, and profile retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.database.connection import get_db
from app.models.db_models import User, Role, LoginHistory, AccessPermission
from app.models.schemas import UserRegister, UserLogin, TokenResponse, UserProfile
from app.security.token_util import hash_password, verify_password, create_access_token
from app.security.rbac import get_current_user
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def generate_ecdh_keypair():
    """Generates a NIST P-256 ECDH key pair."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    return pub_pem, priv_pem

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegister, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username is already taken")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")

    # Find role
    target_role = req.role_name.upper() if req.role_name else "USER"
    role = db.query(Role).filter(Role.role_name == target_role).first()
    if not role:
        role = db.query(Role).filter(Role.role_name == "USER").first()

    # Generate ECDH Keypair
    pub_pem, priv_pem = generate_ecdh_keypair()

    new_user = User(
        user_id=str(uuid.uuid4()),
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        role_id=role.role_id,
        public_key_pem=pub_pem,
        encrypted_private_key=priv_pem,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Add default permissions
    perm = AccessPermission(
        permission_id=str(uuid.uuid4()),
        user_id=new_user.user_id,
        can_upload=True,
        can_export_analytics=True,
        max_shares_per_day=50,
        is_restricted=False
    )
    db.add(perm)
    db.commit()

    token = create_access_token({"sub": new_user.user_id, "username": new_user.username, "role": role.role_name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "role": role.role_name
    }

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLogin, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        # Record failed login
        login_log = LoginHistory(
            user_id=user.user_id if user else None,
            ip_address=client_ip,
            user_agent=user_agent,
            status="FAILURE",
            failure_reason="Invalid credentials",
            attempted_at=datetime.now(timezone.utc)
        )
        db.add(login_log)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled. Contact system administrator.")

    # Record successful login
    login_log = LoginHistory(
        user_id=user.user_id,
        ip_address=client_ip,
        user_agent=user_agent,
        status="SUCCESS",
        attempted_at=datetime.now(timezone.utc)
    )
    db.add(login_log)
    db.commit()

    role_name = user.role.role_name if user.role else "USER"
    token = create_access_token({"sub": user.user_id, "username": user.username, "role": role_name})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
        "role": role_name
    }

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role_name": current_user.role.role_name if current_user.role else "USER",
        "public_key_pem": current_user.public_key_pem,
        "created_at": current_user.created_at
    }
