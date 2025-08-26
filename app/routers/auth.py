from fastapi import APIRouter, HTTPException, status, Depends
from app.models import LoginRequest, SignupRequest, Token, UserResponse
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_admin_user, get_current_user
from app.database import get_collection
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """User login endpoint."""
    user = await authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/signup", response_model=UserResponse)
async def signup(signup_data: SignupRequest, current_admin: UserResponse = Depends(get_current_admin_user)):
    """User signup endpoint (admin only)."""
    users_collection = get_collection("users")
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": signup_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = get_password_hash(signup_data.password)
    
    # Create user document
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc)
    user_doc = {
        "email": signup_data.email,
        "hashed_password": password_hash,
        "role": signup_data.role,
        "is_active": True,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # Insert user
    result = await users_collection.insert_one(user_doc)
    
    # Return user response (without password)
    user_response = UserResponse(
        id=str(result.inserted_id),
        email=signup_data.email,
        role=signup_data.role,
        is_active=True,
        created_at=user_doc["created_at"]
    )
    
    return user_response
