import uuid
from typing import Optional, List

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils.exceptions import (
    UserNotFoundException, 
    EmailAlreadyExistsException, 
    UsernameAlreadyExistsException
)
from app.utils.enums import UserStatus

class UserService:
    """
    Service class for managing user accounts and profiles.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """
        Fetch a user by their UUID.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise UserNotFoundException(detail=f"User with ID {user_id} not found.")
        
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Fetch a user by their @username.
        Useful for internal transfers (Stage 5).
        """
        # Ensure username starts with @
        if not username.startswith("@"):
            username = f"@{username}"
            
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """
        Search for users by username or email (partial match).
        Restricted to ACTIVE users only.
        """
        stmt = select(User).where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            ),
            User.status == UserStatus.ACTIVE
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_user(self, user_id: uuid.UUID, user_update: UserUpdate) -> User:
        """
        Update user profile fields.
        Performs checks to ensure email/username uniqueness if changed.
        """
        user = await self.get_user_by_id(user_id)
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        if not update_data:
            return user

        # 1. Check uniqueness for Email
        if "email" in update_data and update_data["email"] != user.email:
            existing_email = await self.get_user_by_email(update_data["email"])
            if existing_email:
                raise EmailAlreadyExistsException()

        # 2. Check uniqueness for Username (if allowed to update)
        if "username" in update_data and update_data["username"] != user.username:
            existing_username = await self.get_user_by_username(update_data["username"])
            if existing_username:
                raise UsernameAlreadyExistsException()

        # 3. Perform Update
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # 4. Refresh and return
        await self.db.refresh(user)
        return user

    async def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        """
        return user.status == UserStatus.ACTIVE

    async def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.
        """
        return user.is_superuser