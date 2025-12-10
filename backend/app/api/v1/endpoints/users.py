from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate, UserSearchResult
from app.services.user_service import UserService
from app.utils.exceptions import (
    UserNotFoundException, 
    EmailAlreadyExistsException, 
    UsernameAlreadyExistsException
)

router = APIRouter()

@router.get("/search", response_model=UserSearchResult)
async def search_user(
    query: str = Query(..., min_length=3, description="Exact username (@name) or email"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Find a specific user for P2P transfers.
    **PRIVACY FIX:** Only exact matches on Username or Email are returned.
    Partial search is disabled to prevent user database scraping.
    """
    user_service = UserService(db)
    
    # Check if query looks like an email
    if "@" in query and "." in query:
        user = await user_service.get_user_by_email(query)
    elif query.startswith("@"):
        user = await user_service.get_user_by_username(query)
    else:
        # Assume username without @, prepend it
        user = await user_service.get_user_by_username(f"@{query}")
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found."
        )
    
    # Return limited info schema (ID and Username only)
    return UserSearchResult(id=user.id, username=user.username)


@router.patch("/me", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update own user profile.
    """
    user_service = UserService(db)
    try:
        updated_user = await user_service.update_user(
            user_id=current_user.id, 
            user_update=user_update
        )
        await db.commit() # Commit atomic update
        return updated_user
    except (EmailAlreadyExistsException, UsernameAlreadyExistsException) as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=e.detail)


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user details.
    """
    return current_user


# @router.get("/{user_id}", response_model=UserSchema)
# async def read_user_by_id(
#     user_id: uuid.UUID,
#     current_user: User = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db),
# ) -> Any:
#     """
#     Get a specific user by ID.
#     Only open to superusers (admins).
#     """
#     # Check admin privileges manually or use dependency
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, 
#             detail="Not authorized to view other user details."
#         )
        
#     user_service = UserService(db)
#     user = await user_service.get_user_by_id(user_id)
#     return user