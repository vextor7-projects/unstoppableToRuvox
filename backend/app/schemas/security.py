import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from app.utils.enums import Chain
from app.utils.constants import PIN_REGEX

# --- PIN Management Schemas ---

class PinUpdate(BaseModel):
    """
    Schema for requesting a PIN update.
    Requires the current PIN for verification and the new PIN.
    """
    current_pin: str = Field(..., pattern=PIN_REGEX.pattern)
    new_pin: str = Field(..., pattern=PIN_REGEX.pattern)


# --- TOTP (2FA) Management Schemas ---

class TotpSetupResponse(BaseModel):
    """
    Schema for the response when initiating TOTP setup.
    Provides the secret key and a provisioning URI for authenticator apps.
    """
    secret_key: str
    provisioning_uri: str

class TotpVerifyRequest(BaseModel):
    """
    Schema for verifying a TOTP code during setup or login.
    """
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

class TotpDisableRequest(BaseModel):
    """
    Schema for disabling TOTP. Requires a valid code or a backup code.
    """
    code: str = Field(..., min_length=6, max_length=8, pattern=r"^\d{6,8}$") # Can be 6-digit TOTP or 8-digit backup

class TotpBackupCodesResponse(BaseModel):
    """
    Schema for the response containing generated TOTP backup codes.
    These should be displayed to the user only once.
    """
    backup_codes: List[str]


# --- Address Whitelist Schemas ---

class AddressWhitelistBase(BaseModel):
    """
    Base schema for address whitelist entries.
    """
    chain: Chain
    address: str
    label: str = Field(..., min_length=1, max_length=100)

class AddressWhitelistCreate(AddressWhitelistBase):
    """
    Schema for adding a new address to the whitelist.
    """
    pass

class AddressWhitelistEntry(AddressWhitelistBase):
    """
    Schema representing a whitelist entry returned by the API.
    Includes the database ID.
    """
    id: uuid.UUID

    class Config:
        from_attributes = True

# --- General Security Status ---

class SecurityStatusResponse(BaseModel):
    """
    Schema for returning the user's current security settings status.
    """
    is_pin_set: bool = True # PIN is mandatory
    is_biometric_enabled: Optional[bool] = None # Frontend specific, but API can hint
    is_totp_enabled: bool
    kyc_level: str # Using string representation of the enum
