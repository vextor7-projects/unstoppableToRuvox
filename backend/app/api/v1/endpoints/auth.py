from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.token import Token, RefreshTokenRequest
from app.schemas.user import UserCreate, User as UserSchema
from app.services.auth_service import AuthService
from app.utils.exceptions import InvalidCredentialsException, BadRequestException

router = APIRouter()

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user.
    
    - **email**: Must be unique.
    - **username**: Must start with '@' and be unique.
    - **pin**: 6-digit numeric PIN.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    - **username**: Can be either the user's email or username (starting with @).
    - **password**: The user's 6-digit PIN.
    """
    auth_service = AuthService(db)
    
    # The OAuth2 spec uses 'username' and 'password' fields.
    # We map 'form_data.username' to our identifier (email/username)
    # and 'form_data.password' to our PIN.
    token = await auth_service.login(
        identifier=form_data.username,
        pin=form_data.password
    )
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a new access token using a refresh token.
    Currently returns a simplified structure; robust implementation would 
    verify the refresh token against a whitelist/blacklist in DB/Redis.
    """
    # NOTE: For a production-grade system (Stage 3), you should validate 
    # the refresh token against the database or Redis to ensure it hasn't 
    # been revoked (e.g., on logout).
    # For now, we rely on the JWT signature validation in the dependency
    # or assume the client handles the logic.
    
    # Implementation of refresh logic typically belongs in AuthService
    # For this initial pass, we acknowledge the endpoint exists.
    # A full implementation requires decoding the refresh token 
    # and re-issuing credentials.
    
    # Placeholder: Real logic requires AuthService expansion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Refresh token logic to be implemented in AuthService."
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Logout the current user.
    Since we use stateless JWTs, this is mostly a client-side action (discarding the token).
    However, this endpoint is useful if we implement a token blacklist in Redis later.
    """
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user details.
    Useful for the mobile app to fetch profile info on startup.
    """
    return current_user