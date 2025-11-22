import uuid
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """
    Schema for the token response returned upon successful login.
    Includes both the access token and the refresh token.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """
    Schema representing the data stored within the JWT payload ('sub' claim).
    Corresponds to the `subject` used when creating the token.
    """
    sub: Optional[uuid.UUID] = None # Using UUID for user ID

class RefreshTokenRequest(BaseModel):
    """
    Schema for the request body when refreshing an access token.
    """
    refresh_token: str
