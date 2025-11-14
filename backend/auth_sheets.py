"""
Google Sheets-only Authentication Service
No PostgreSQL - ALL authentication data stored in Google Sheets
"""
import bcrypt
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

from sheets_client import SheetsClient


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str


class AuthTokenResponse(BaseModel):
    auth_token: str
    user_id: str
    email: str
    expires_at: str


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_auth_token() -> str:
    """Generate a secure random bearer token"""
    return secrets.token_urlsafe(32)


class SheetsAuthService:
    """Authentication service using only Google Sheets"""
    
    def __init__(self, sheets_client: SheetsClient):
        self.sheets = sheets_client
        self.token_expiry_days = 7
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up user by email in Google Sheets User table"""
        users = self.sheets.read_sheet("User")
        for user in users:
            if user.get("email") == email:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Look up user by ID in Google Sheets User table"""
        users = self.sheets.read_sheet("User")
        for user in users:
            if user.get("id") == user_id:
                return user
        return None
    
    def validate_token(self, auth_token: str) -> Optional[str]:
        """
        Validate bearer token by checking Session table in Google Sheets
        Returns user_id if valid, None if invalid/expired
        """
        print(f"[DEBUG validate_token] Looking for token: {auth_token}")
        sessions = self.sheets.read_sheet("Session")
        print(f"[DEBUG validate_token] Found {len(sessions)} sessions total")
        
        for idx, session in enumerate(sessions):
            session_token = session.get("auth_token", "")
            print(f"[DEBUG validate_token] Session {idx}: auth_token={session_token[:20] if session_token else 'EMPTY'}... (matches: {session_token == auth_token})")
            
            if session.get("auth_token") == auth_token:
                print(f"[DEBUG validate_token] Token matched! Checking expiration...")
                expires_at_str = session.get("expires_at")
                print(f"[DEBUG validate_token] expires_at from sheet: {expires_at_str}")
                
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        print(f"[DEBUG validate_token] expires_at={expires_at}, now={now}, valid={expires_at > now}")
                        if expires_at > datetime.now(timezone.utc):
                            user_id = session.get("user_id")
                            print(f"[DEBUG validate_token] Token is valid! Returning user_id: {user_id}")
                            return user_id
                        else:
                            print(f"[DEBUG validate_token] Token expired!")
                    except (ValueError, AttributeError) as e:
                        print(f"[DEBUG validate_token] Error parsing expiration: {e}")
                        continue
        
        print(f"[DEBUG validate_token] Token NOT found or expired. Returning None.")
        return None
    
    def register(self, request: RegisterRequest) -> UserResponse:
        """
        Register a new user - creates ONLY User in Google Sheets (NOT Session).
        User must login separately to get auth token.
        
        User table schema (7 columns):
        [id, email, password, full_name, role, created_at, last_login]
        """
        if self.get_user_by_email(request.email):
            raise ValueError(f"User with email {request.email} already exists")
        
        user_id = self.sheets.generate_next_id("User", "USR")
        
        password_hash = hash_password(request.password)
        created_at = datetime.now(timezone.utc).isoformat()
        
        full_name = f"{request.first_name or ''} {request.last_name or ''}".strip() or request.email
        
        user_row = [
            user_id,
            request.email,
            password_hash,
            full_name,
            "user",
            created_at,
            ""
        ]
        
        self.sheets.append_row("User", user_row)
        
        return UserResponse(
            user_id=user_id,
            email=request.email
        )
    
    def login(self, request: LoginRequest) -> AuthTokenResponse:
        """
        Login existing user - verifies password and creates Session in Google Sheets
        """
        user = self.get_user_by_email(request.email)
        
        if not user:
            raise ValueError("Invalid email or password")
        
        password_hash = user.get("password")
        if not password_hash or not verify_password(request.password, password_hash):
            raise ValueError("Invalid email or password")
        
        auth_token = generate_auth_token()
        session_id = self.sheets.generate_next_id("Session", "SES")
        created_at = datetime.now(timezone.utc).isoformat()
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.token_expiry_days)
        
        session_row = [
            session_id,
            user.get("id"),
            auth_token,
            created_at,
            expires_at.isoformat()
        ]
        
        self.sheets.append_row("Session", session_row)
        
        users = self.sheets.read_sheet("User")
        for i, u in enumerate(users):
            if u.get("id") == user.get("id"):
                updated_user_row = [
                    user.get("id"),
                    user.get("email"),
                    user.get("password"),
                    user.get("full_name"),
                    user.get("role", "user"),
                    user.get("created_at"),
                    created_at
                ]
                self.sheets.update_row("User", i + 2, updated_user_row)
                break
        
        return AuthTokenResponse(
            auth_token=auth_token,
            user_id=user.get("id") or "",
            email=user.get("email") or "",
            expires_at=expires_at.isoformat()
        )
