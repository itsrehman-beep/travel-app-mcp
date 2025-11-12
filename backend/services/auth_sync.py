"""
Authentication synchronization service for dual-write to PostgreSQL and Google Sheets.
Ensures User and Session data is consistently stored in both systems.
"""
from datetime import datetime, timezone
from typing import Optional
from auth import (
    User, RegisterRequest, LoginRequest, AuthResponse,
    hash_password, verify_password, generate_token, SessionLocal
)
from sheets_client import sheets_client


def create_user_with_session(request: RegisterRequest) -> AuthResponse:
    """
    Register a new user with dual-write to PostgreSQL and Google Sheets.
    Creates both User and Session records.
    
    Flow:
    1. Generate sequential user ID from Google Sheets
    2. Create user in PostgreSQL (with rollback on failure)
    3. Write user to Google Sheets User table
    4. Generate JWT token
    5. Write session to Google Sheets Session table
    
    Args:
        request: Registration request with email, password, names
    
    Returns:
        AuthResponse with JWT token and user info
    
    Raises:
        Exception: If user exists or any step fails
    """
    db = SessionLocal()
    try:
        # Step 1: Generate sequential User ID
        user_id = sheets_client.generate_next_id('User', 'USR', width=4)
        
        # Step 2: Check if user already exists in PostgreSQL
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise Exception('User with this email already exists')
        
        # Step 3: Create user in PostgreSQL
        password_hash = hash_password(request.password)
        created_at = datetime.now(timezone.utc)
        
        new_user = User(
            id=user_id,
            email=request.email,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name,
            created_at=created_at,
            updated_at=created_at
        )
        
        db.add(new_user)
        # Flush to catch integrity errors (unique email, etc.) BEFORE Sheets writes
        # This triggers SQL constraints without committing the transaction
        db.flush()
        
        # Step 4: Write user to Google Sheets (NEVER store plaintext password!)
        # Store password_hash for consistency, or use a sentinel value
        full_name = f"{request.first_name or ''} {request.last_name or ''}".strip() or request.email
        user_row = [
            user_id,
            request.email,
            password_hash,  # Hashed password, never plaintext
            full_name,
            'user',  # role
            created_at.isoformat(),
            None  # last_login
        ]
        
        sheets_success = sheets_client.append_row('User', user_row)
        if not sheets_success:
            # Rollback: abort transaction before committing
            db.rollback()
            raise Exception('Failed to write user to Google Sheets')
        
        # Step 5: Generate JWT token
        token = generate_token(user_id, request.email)
        
        # Step 6: Create session in Google Sheets
        session_id = sheets_client.generate_next_id('Session', 'SES', width=4)
        expires_at = datetime.now(timezone.utc)
        from auth import JWT_EXPIRATION_HOURS
        from datetime import timedelta
        expires_at = created_at + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        session_row = [
            session_id,
            user_id,
            token,
            created_at.isoformat(),
            expires_at.isoformat()
        ]
        
        session_success = sheets_client.append_row('Session', session_row)
        if not session_success:
            # Critical: Session creation is part of registration contract
            db.rollback()
            raise Exception('Failed to create session in Google Sheets')
        
        # ONLY NOW commit to PostgreSQL after both Sheets writes succeeded
        db.commit()
        
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            email=request.email
        )
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def login_user_with_session(request: LoginRequest) -> AuthResponse:
    """
    Login a user and create session in Google Sheets.
    
    Flow:
    1. Find user in PostgreSQL and verify password
    2. Generate JWT token
    3. Write session to Google Sheets Session table
    4. Update last_login in Google Sheets User table
    
    Args:
        request: Login request with email and password
    
    Returns:
        AuthResponse with JWT token and user info
    
    Raises:
        Exception: If credentials invalid or user inactive
    """
    db = SessionLocal()
    try:
        # Step 1: Find user in PostgreSQL
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise Exception('Invalid email or password')
        
        # Step 2: Verify password
        if not verify_password(request.password, user.password_hash):
            raise Exception('Invalid email or password')
        
        # Step 3: Check if user is active
        if not user.is_active:
            raise Exception('User account is deactivated')
        
        # Step 4: Generate JWT token
        token = generate_token(user.id, user.email)
        
        # Step 5: Create session in Google Sheets
        session_id = sheets_client.generate_next_id('Session', 'SES', width=4)
        created_at = datetime.now(timezone.utc)
        
        from auth import JWT_EXPIRATION_HOURS
        from datetime import timedelta
        expires_at = created_at + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        session_row = [
            session_id,
            user.id,
            token,
            created_at.isoformat(),
            expires_at.isoformat()
        ]
        
        session_success = sheets_client.append_row('Session', session_row)
        if not session_success:
            print(f"Warning: Failed to create session record for user {user.id}")
        
        # Step 6: Update last_login in Google Sheets User table (optional, best-effort)
        try:
            user_result = sheets_client.find_row_by_id('User', user.id)
            if user_result:
                row_index, user_data = user_result
                # Update last_login (column G, index 6)
                user_row = [
                    user.id,
                    user.email,
                    user.password_hash,
                    f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                    'user',  # role
                    user_data.get('created_at', created_at.isoformat()),
                    created_at.isoformat()  # last_login
                ]
                sheets_client.update_row('User', row_index - 1, user_row)
        except Exception as e:
            print(f"Warning: Failed to update last_login in Sheets: {e}")
        
        return AuthResponse(
            access_token=token,
            user_id=user.id,
            email=user.email
        )
        
    finally:
        db.close()
