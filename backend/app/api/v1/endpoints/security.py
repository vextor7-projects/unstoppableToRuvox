from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.security import (
    PinUpdate, 
    TotpSetupResponse, 
    TotpVerifyRequest, 
    TotpDisableRequest, 
    TotpBackupCodesResponse,
    AddressWhitelistCreate,
    AddressWhitelistEntry,
    SecurityStatusResponse
)
from app.services.security_service import SecurityService
from app.utils.exceptions import (
    InvalidCredentialsException,
    BadRequestException,
    InvalidTotpCodeException,
    ConflictException,
    NotFoundException
)

router = APIRouter()

# --- PIN Management ---

@router.post("/pin/update", status_code=status.HTTP_200_OK)
async def update_pin(
    pin_update: PinUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update the user's 6-digit PIN.
    Requires the current PIN for verification.
    """
    security_service = SecurityService(db)
    await security_service.update_pin(current_user.id, pin_update)
    return {"message": "PIN updated successfully."}


# --- TOTP (2FA) Management ---

@router.get("/totp/setup", response_model=TotpSetupResponse)
async def setup_totp(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Initiate TOTP setup.
    Returns a secret key and a provisioning URI (for QR code generation on the client).
    """
    security_service = SecurityService(db)
    return await security_service.initiate_totp_setup(current_user.id)


@router.post("/totp/enable", response_model=TotpBackupCodesResponse)
async def enable_totp(
    verify_req: TotpVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Finalize TOTP setup by verifying a code.
    If successful, 2FA is enabled and backup codes are returned.
    """
    security_service = SecurityService(db)
    backup_codes = await security_service.enable_totp(current_user.id, verify_req)
    return {"backup_codes": backup_codes}


@router.post("/totp/disable", status_code=status.HTTP_200_OK)
async def disable_totp(
    disable_req: TotpDisableRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Disable TOTP 2FA.
    Requires a valid OTP code (or backup code) for security.
    """
    security_service = SecurityService(db)
    await security_service.disable_totp(current_user.id, disable_req.code)
    return {"message": "2FA disabled successfully."}


@router.post("/totp/verify", response_model=bool)
async def verify_totp_code(
    verify_req: TotpVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify a TOTP code (useful for re-authentication before sensitive actions).
    Returns True if valid, raises 400 if invalid.
    """
    security_service = SecurityService(db)
    is_valid = await security_service.verify_totp(current_user.id, verify_req.code)
    
    if not is_valid:
        raise InvalidTotpCodeException()
        
    return True


# --- Address Whitelist Management ---

@router.get("/whitelist", response_model=List[AddressWhitelistEntry])
async def get_whitelist(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the user's list of whitelisted withdrawal addresses.
    """
    security_service = SecurityService(db)
    return await security_service.get_whitelist(current_user.id)


@router.post("/whitelist", response_model=AddressWhitelistEntry)
async def add_whitelist_address(
    entry_in: AddressWhitelistCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a new address to the whitelist.
    """
    security_service = SecurityService(db)
    return await security_service.add_whitelist_address(current_user.id, entry_in)


@router.delete("/whitelist/{entry_id}", status_code=status.HTTP_200_OK)
async def delete_whitelist_address(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove an address from the whitelist.
    """
    security_service = SecurityService(db)
    await security_service.delete_whitelist_address(current_user.id, entry_id)
    return {"message": "Address removed from whitelist."}


# --- General Security Status ---

@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get an overview of the user's security settings (2FA status, KYC level).
    Useful for the frontend 'Security' settings page.
    """
    # We need to check UserSecurity to see if TOTP is enabled
    # (Assuming user.security relation is loaded or we fetch it)
    
    # Simple query to check TOTP status if not joined loaded
    # For optimized performance, we might want to eager load 'security' in get_current_user
    # But here is a safe fallback:
    
    is_totp = False
    if current_user.security:
        is_totp = current_user.security.totp_enabled
    
    return {
        "is_pin_set": True, # Always true for active users
        "is_totp_enabled": is_totp,
        "kyc_level": current_user.kyc_level.value,
        "is_biometric_enabled": None # Client-side setting usually
    }