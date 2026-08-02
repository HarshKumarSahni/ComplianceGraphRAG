import jwt
from datetime import datetime, timedelta
from typing import Optional
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import BaseAppException
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, settings: Settings):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """Hash a plain text password using PBKDF2-SHA256."""
        return pbkdf2_sha256.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a stored hash (supports pbkdf2_sha256 and bcrypt)."""
        try:
            if hashed_password and (hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$")):
                from passlib.hash import bcrypt
                return bcrypt.verify(plain_password, hashed_password)
            return pbkdf2_sha256.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

    def create_access_token(self, user: User) -> str:
        """Create a signed JWT access token containing user identity claims."""
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        payload = {
            "sub": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token signature expired.")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def register_user(self, db: Session, req: SignupRequest) -> TokenResponse:
        """Register a new user in the database and return authentication token."""
        existing_user = db.query(User).filter(User.email == req.email.lower().strip()).first()
        if existing_user:
            raise BaseAppException(
                message="An account with this email address already exists.",
                status_code=400
            )

        hashed_pwd = self.hash_password(req.password)
        new_user = User(
            full_name=req.full_name.strip(),
            email=req.email.lower().strip(),
            hashed_password=hashed_pwd,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"Successfully registered new user: {new_user.email} (ID: {new_user.id})")
        token = self.create_access_token(new_user)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user)
        )

    def authenticate_user(self, db: Session, req: LoginRequest) -> TokenResponse:
        """Authenticate user credentials and return access token."""
        user = db.query(User).filter(User.email == req.email.lower().strip()).first()
        if not user or not self.verify_password(req.password, user.hashed_password):
            raise BaseAppException(
                message="Invalid email address or password.",
                status_code=401
            )

        if not user.is_active:
            raise BaseAppException(
                message="Account is deactivated. Please contact support.",
                status_code=403
            )

        logger.info(f"User authenticated successfully: {user.email}")
        token = self.create_access_token(user)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
