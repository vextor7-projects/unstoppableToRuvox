from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.utils.enums import UserRole, UserStatus, KycStatus
from app.utils.exceptions import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    BadRequestException
)

class AuthService:
    """
    Service class for handling authentication and user registration logic.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_in: UserCreate) -> User:
        """
        Registers a new user.
        Checks for existing email/username, hashes the PIN, and creates the user record.
        """
        # 1. Check for existing email or username
        # We do this in one query for efficiency
        stmt = select(User).where(
            or_(
                User.email == user_in.email,
                User.username == user_in.username
            )
        )
        result = await self.db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.email == user_in.email:
                raise EmailAlreadyExistsException()
            else:
                raise UsernameAlreadyExistsException()

        # 2. Hash the PIN
        hashed_pin = get_password_hash(user_in.pin)

        # 3. Create the User object
        # We don't set 'hashed_pin' directly in the constructor if using Pydantic v2 model_dump
        # because 'hashed_pin' isn't in UserCreate. We map it explicitly.
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_pin=hashed_pin,
            role=user_in.role,
            status=UserStatus.ACTIVE,
            kyc_level=KycStatus.NOT_STARTED,
            is_superuser=False
        )

        # 4. Persist to Database
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user

    async def authenticate_user(self, identifier: str, pin: str) -> Optional[User]:
        """
        Authenticates a user by email OR username and PIN.
        Returns the user object if successful, None otherwise.
        """
        # 1. Fetch user by email or username
        stmt = select(User).where(
            or_(
                User.email == identifier,
                User.username == identifier
            )
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        # 2. Verify User and PIN
        if not user:
            return None
        
        if not verify_password(pin, user.hashed_pin):
            return None

        return user

    async def login(self, identifier: str, pin: str) -> Token:
        """
        Performs the full login flow: authenticate and generate tokens.
        """
        user = await self.authenticate_user(identifier, pin)
        
        if not user:
            raise InvalidCredentialsException()

        if user.status != UserStatus.ACTIVE:
            raise BadRequestException(detail="Account is inactive or suspended.")

        # 3. Generate Tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), # Subject is the User UUID
            expires_delta=access_token_expires
        )
        
        # Refresh token (longer lived)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_access_token(
            subject=str(user.id),
            expires_delta=refresh_token_expires
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )