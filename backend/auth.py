import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pydantic import BaseModel

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception('DATABASE_URL environment variable not set')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# JWT secret - strict enforcement
JWT_SECRET = os.environ.get('SESSION_SECRET')
if not JWT_SECRET:
    raise Exception('SESSION_SECRET environment variable must be set')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Models using SQLAlchemy 2.0 style
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# Pydantic models for validation
class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id: str
    email: str

class UserInfo(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_token(user_id: str, email: str) -> str:
    """Generate a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate a JWT token and return the payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_user_id() -> str:
    """Generate a unique user ID"""
    import uuid
    return f"USR{str(uuid.uuid4().hex[:10]).upper()}"

# Authentication functions
def register_user(request: RegisterRequest) -> AuthResponse:
    """Register a new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise Exception('User with this email already exists')
        
        # Create new user
        user_id = generate_user_id()
        password_hash = hash_password(request.password)
        
        new_user = User(
            id=user_id,
            email=request.email,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        db.add(new_user)
        db.commit()
        
        # Generate token
        token = generate_token(user_id, request.email)
        
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            email=request.email
        )
    finally:
        db.close()

def login_user(request: LoginRequest) -> AuthResponse:
    """Login a user"""
    db = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise Exception('Invalid email or password')
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise Exception('Invalid email or password')
        
        # Check if user is active
        if not user.is_active:
            raise Exception('User account is deactivated')
        
        # Generate token
        token = generate_token(user.id, user.email)
        
        return AuthResponse(
            access_token=token,
            user_id=user.id,
            email=user.email
        )
    finally:
        db.close()

def get_user_from_token(token: str) -> Optional[UserInfo]:
    """Get user information from a JWT token"""
    payload = validate_token(token)
    if not payload:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload['user_id']).first()
        if not user or not user.is_active:
            return None
        
        return UserInfo(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at
        )
    finally:
        db.close()

def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from a JWT token"""
    payload = validate_token(token)
    return payload.get('user_id') if payload else None
