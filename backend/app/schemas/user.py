import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.utils.enums import UserRole, KycStatus, UserStatus
from app.utils.constants import USERNAME_REGEX, PIN_REGEX

# --- Base Schemas ---

class UserBase(BaseModel):
    """
    Base schema for User data, containing common fields.
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, pattern=USERNAME_REGEX.pattern)
    phone_number: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    status: Optional[UserStatus] = UserStatus.ACTIVE

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2


# --- Schemas for API Input (Create/Update) ---

class UserCreate(UserBase):
    """
    Schema for creating a new user. Requires email, username, and pin.
    """
    email: EmailStr
    username: str = Field(..., pattern=USERNAME_REGEX.pattern)
    pin: str = Field(..., pattern=PIN_REGEX.pattern) # Plain PIN for creation

    @validator('username')
    def username_must_start_with_at(cls, v):
        if not v.startswith('@'):
            raise ValueError('Username must start with @')
        return v

class UserUpdate(UserBase):
    """
    Schema for updating an existing user. All fields are optional.
    PIN cannot be updated here (use a dedicated endpoint).
    Role/Status/is_superuser updates should typically be admin-only actions.
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, pattern=USERNAME_REGEX.pattern)
    phone_number: Optional[str] = None
    # role: Optional[UserRole] = None # Generally updated by admin
    # status: Optional[UserStatus] = None # Generally updated by admin
    # is_superuser: Optional[bool] = None # Generally updated by admin

    @validator('username')
    def username_must_start_with_at(cls, v):
        if v is not None and not v.startswith('@'):
            raise ValueError('Username must start with @')
        return v


# --- Schemas for Database Interaction ---

class UserInDBBase(UserBase):
    """
    Base schema representing User data as stored in the database.
    Includes database-specific fields like id, created_at, updated_at.
    """
    id: uuid.UUID
    email: EmailStr
    username: str
    phone_number: Optional[str] = None
    role: UserRole
    kyc_level: KycStatus
    status: UserStatus
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

class UserInDB(UserInDBBase):
    """
    Schema representing User data directly from the database, including hashed_pin.
    Should generally not be exposed directly via API.
    """
    hashed_pin: str


# --- Schemas for API Output ---

class User(UserInDBBase):
    """
    Schema representing User data returned by the API.
    Excludes sensitive fields like hashed_pin.
    """
    pass # Inherits all fields from UserInDBBase


# --- Other User-Related Schemas ---

class UserSearchResult(BaseModel):
    """
    Schema for returning user search results (e.g., for internal transfers).
    """
    id: uuid.UUID
    username: str

    class Config:
        from_attributes = True
