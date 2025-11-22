import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.crud.base import BaseCRUD
from app.models.user import User, UserSecurity, AddressWhitelist
from app.schemas.security import AddressWhitelistCreate
from app.schemas.user import UserCreate, UserUpdate
from app.utils.enums import Chain


class CRUDUser(BaseCRUD[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User, UserSecurity, and AddressWhitelist models.
    """

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user, user_security, and initial vip_tier entry.
        
        This overrides the base `create` method to handle:
        1. Hashing the plain-text PIN.
        2. Creating the associated `UserSecurity` object.
        """
        # Create a dictionary from the UserCreate schema
        obj_in_data = obj_in.model_dump(exclude={"pin"})
        
        # Hash the PIN
        hashed_pin = get_password_hash(obj_in.pin)
        
        # Create the User model instance
        db_obj = self.model(**obj_in_data, hashed_pin=hashed_pin)
        
        # Create the associated UserSecurity object
        # This will be automatically linked via the back_populates
        db_security_obj = UserSecurity(user=db_obj, totp_enabled=False)
        
        # Add both to the session
        db.add(db_obj)
        db.add(db_security_obj)
        
        # Commit the transaction to save both objects
        await db.commit()
        
        # Refresh the main user object to get DB-generated values
        await db.refresh(db_obj)
        
        return db_obj

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        """
        stmt = select(self.model).filter(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        Get a user by their username (e.g., "@username").
        """
        stmt = select(self.model).filter(self.model.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, *, phone_number: str) -> Optional[User]:
        """
        Get a user by their phone number.
        """
        stmt = select(self.model).filter(self.model.phone_number == phone_number)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(
        self, db: AsyncSession, *, identifier: str
    ) -> Optional[User]:
        """
        Get a user by either their email or username.
        """
        stmt = select(self.model).filter(
            (self.model.email == identifier) | (self.model.username == identifier)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(
        self, db: AsyncSession, *, email_or_username: str, pin: str
    ) -> Optional[User]:
        """
        Authenticate a user by email/username and PIN.
        
        :return: The User object if authentication is successful, None otherwise.
        """
        user = await self.get_by_email_or_username(db, identifier=email_or_username)
        if not user:
            return None
        if not verify_password(pin, user.hashed_pin):
            return None
        return user

    def is_superuser(self, user: User) -> bool:
        """
        Check if a user has superuser privileges.
        """
        return user.is_superuser

    async def get_security(self, db: AsyncSession, *, user: User) -> Optional[UserSecurity]:
        """
        Get the UserSecurity object associated with a user.
        """
        # Use selectinload to ensure the relationship is loaded
        stmt = (
            select(User)
            .options(selectinload(User.security))
            .filter(User.id == user.id)
        )
        result = await db.execute(stmt)
        user_with_security = result.scalar_one_or_none()
        return user_with_security.security if user_with_security else None

    # --- Address Whitelist CRUD Methods ---

    async def get_whitelist_entry(
        self, db: AsyncSession, *, user: User, entry_id: uuid.UUID
    ) -> Optional[AddressWhitelist]:
        """
        Get a specific whitelist entry by its ID, ensuring it belongs to the user.
        """
        stmt = select(AddressWhitelist).filter(
            AddressWhitelist.id == entry_id, AddressWhitelist.user_id == user.id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_whitelist_entry_by_details(
        self, db: AsyncSession, *, user: User, address: str, chain: Chain
    ) -> Optional[AddressWhitelist]:
        """
        Get a specific whitelist entry by its content, ensuring it belongs to the user.
        """
        stmt = select(AddressWhitelist).filter(
            AddressWhitelist.user_id == user.id,
            AddressWhitelist.address == address,
            AddressWhitelist.chain == chain,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_whitelist(
        self, db: AsyncSession, *, user: User
    ) -> List[AddressWhitelist]:
        """
        Get all whitelist entries for a specific user.
        """
        stmt = (
            select(AddressWhitelist)
            .filter(AddressWhitelist.user_id == user.id)
            .order_by(AddressWhitelist.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def add_whitelist_address(
        self, db: AsyncSession, *, user: User, obj_in: AddressWhitelistCreate
    ) -> AddressWhitelist:
        """
        Create a new whitelist entry for a user.
        """
        db_obj = AddressWhitelist(**obj_in.model_dump(), user_id=user.id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove_whitelist_address(
        self, db: AsyncSession, *, db_obj: AddressWhitelist
    ) -> AddressWhitelist:
        """
        Remove a whitelist entry from the database.
        Assumes the entry object (db_obj) was already retrieved and verified.
        """
        await db.delete(db_obj)
        await db.commit()
        return db_obj


# Instantiate the CRUD object for use in the application
crud_user = CRUDUser(User)