import uuid
import pyotp
import json
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    get_password_hash, 
    verify_password, 
    encrypt_data, 
    decrypt_data
)
from app.models.user import User, UserSecurity, AddressWhitelist
from app.schemas.security import (
    PinUpdate, 
    AddressWhitelistCreate, 
    TotpSetupResponse,
    TotpVerifyRequest
)
from app.utils.enums import Chain
from app.utils.exceptions import (
    InvalidCredentialsException,
    BadRequestException,
    NotFoundException,
    InvalidTotpCodeException,
    ConflictException,
    EncryptionException
)
from app.utils.helpers import generate_totp_backup_codes

class SecurityService:
    """
    Service class for managing advanced user security features:
    - PIN updates
    - TOTP (2FA) setup and verification
    - Address Whitelisting
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- PIN Management ---

    async def update_pin(self, user_id: uuid.UUID, pin_update: PinUpdate) -> None:
        """
        Update user's 6-digit PIN.
        Requires verifying the old PIN first.
        """
        # Fetch user
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise NotFoundException(detail="User not found.")

        # Verify old PIN
        if not verify_password(pin_update.current_pin, user.hashed_pin):
            raise InvalidCredentialsException(detail="Current PIN is incorrect.")

        # Hash and set new PIN
        user.hashed_pin = get_password_hash(pin_update.new_pin)
        self.db.add(user)
        await self.db.commit()


    # --- TOTP (2FA) Management ---

    async def initiate_totp_setup(self, user_id: uuid.UUID) -> TotpSetupResponse:
        """
        Generate a new TOTP secret for a user to scan.
        Does NOT enable 2FA yet; user must verify a code first.
        """
        # Generate a random base32 secret
        secret = pyotp.random_base32()
        
        # Create provisioning URI for QR code (e.g., Google Authenticator)
        # Format: otpauth://totp/Ruvox:user@example.com?secret=XYZ&issuer=Ruvox
        user_stmt = select(User).where(User.id == user_id)
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalars().first()
        
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email, 
            issuer_name="Ruvox Wallet"
        )
        
        # Temporarily store secret? 
        # In a strict flow, we might store this in Redis with a short TTL.
        # For simplicity/persistence, we can store it in UserSecurity but keep totp_enabled=False.
        
        await self._save_totp_secret(user_id, secret, enabled=False)
        
        return TotpSetupResponse(secret_key=secret, provisioning_uri=provisioning_uri)

    async def enable_totp(self, user_id: uuid.UUID, verify_req: TotpVerifyRequest) -> List[str]:
        """
        Finalize TOTP setup by verifying a code.
        If successful, enables 2FA and returns backup codes.
        """
        security_record = await self._get_or_create_security_record(user_id)
        
        if not security_record.totp_secret:
            raise BadRequestException(detail="TOTP setup not initiated.")
            
        # Decrypt secret to verify code
        secret = decrypt_data(security_record.totp_secret)
        if not secret:
            raise EncryptionException(detail="Failed to decrypt security settings.")
            
        totp = pyotp.TOTP(secret)
        if not totp.verify(verify_req.code):
            raise InvalidTotpCodeException()
            
        # Code valid -> Enable TOTP
        security_record.totp_enabled = True
        
        # Generate and store backup codes
        backup_codes = generate_totp_backup_codes()
        # Encrypt backup codes as a JSON string
        encrypted_codes = encrypt_data(json.dumps(backup_codes))
        security_record.hashed_backup_codes = encrypted_codes
        
        self.db.add(security_record)
        await self.db.commit()
        
        return backup_codes

    async def verify_totp(self, user_id: uuid.UUID, code: str, strict: bool = False) -> bool:
        """
        Verify a TOTP code.
        :param strict: If True, returns False if TOTP is NOT enabled (Safe for Withdrawals).
                       If False, returns True if TOTP is NOT enabled (Safe for Login).
        """
        security_record = await self._get_or_create_security_record(user_id)
        
        # STRICT MODE LOGIC FIX
        if not security_record.totp_enabled or not security_record.totp_secret:
            if strict:
                return False # Fail secure
            return True # Allow pass (e.g. login for user without 2FA)
            
        # 1. Check standard TOTP (6 digits)
        if len(code) == 6:
            secret = decrypt_data(security_record.totp_secret)
            if not secret:
                raise EncryptionException()
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
            
        # 2. Check backup codes (8 digits)
        elif len(code) == 8:
            if not security_record.hashed_backup_codes:
                return False
                
            backup_codes_json = decrypt_data(security_record.hashed_backup_codes)
            if not backup_codes_json:
                raise EncryptionException()
                
            backup_codes = json.loads(backup_codes_json)
            
            if code in backup_codes:
                # Burn the used code (requires DB write)
                backup_codes.remove(code)
                security_record.hashed_backup_codes = encrypt_data(json.dumps(backup_codes))
                self.db.add(security_record)
                await self.db.flush() # Caller must commit
                return True
                
        return False


    async def disable_totp(self, user_id: uuid.UUID, code: str) -> None:
        """
        Disable 2FA. Requires a valid code (or backup code) to perform this dangerous action.
        """
        is_valid = await self.verify_totp(user_id, code)
        if not is_valid:
            raise InvalidTotpCodeException()
            
        security_record = await self._get_or_create_security_record(user_id)
        security_record.totp_enabled = False
        security_record.totp_secret = None
        security_record.hashed_backup_codes = None
        
        self.db.add(security_record)
        await self.db.commit()


    # --- Address Whitelist Management ---

    async def add_whitelist_address(
        self, user_id: uuid.UUID, entry_in: AddressWhitelistCreate
    ) -> AddressWhitelist:
        """
        Add an address to the user's withdrawal whitelist.
        """
        # Check for duplicates
        stmt = select(AddressWhitelist).where(
            AddressWhitelist.user_id == user_id,
            AddressWhitelist.chain == entry_in.chain,
            AddressWhitelist.address == entry_in.address
        )
        existing = await self.db.execute(stmt)
        if existing.scalars().first():
            raise ConflictException(detail="Address already in whitelist.")
            
        # Verify address format (basic check, deeper check in wallet service)
        if len(entry_in.address) < 10: # Simple sanity check
            raise BadRequestException(detail="Invalid address format.")

        entry = AddressWhitelist(
            user_id=user_id,
            chain=entry_in.chain,
            address=entry_in.address,
            label=entry_in.label
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_whitelist(self, user_id: uuid.UUID) -> List[AddressWhitelist]:
        """
        Get all whitelisted addresses for a user.
        """
        stmt = select(AddressWhitelist).where(AddressWhitelist.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_whitelist_address(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        """
        Remove an address from the whitelist.
        """
        stmt = select(AddressWhitelist).where(
            AddressWhitelist.id == entry_id,
            AddressWhitelist.user_id == user_id
        )
        result = await self.db.execute(stmt)
        entry = result.scalars().first()
        
        if not entry:
            raise NotFoundException(detail="Whitelist entry not found.")
            
        await self.db.delete(entry)
        await self.db.commit()


    # --- Internal Helpers ---

    async def _save_totp_secret(self, user_id: uuid.UUID, secret: str, enabled: bool = False):
        """
        Helper to encrypt and save the TOTP secret to the UserSecurity table.
        """
        security_record = await self._get_or_create_security_record(user_id)
        
        encrypted_secret = encrypt_data(secret)
        if not encrypted_secret:
            raise EncryptionException(detail="Encryption failed.")
            
        security_record.totp_secret = encrypted_secret
        security_record.totp_enabled = enabled
        
        self.db.add(security_record)
        await self.db.commit()

    async def _get_or_create_security_record(self, user_id: uuid.UUID) -> UserSecurity:
        """
        Fetches the UserSecurity record or creates one if it doesn't exist.
        Ensures 1:1 relationship integrity.
        """
        stmt = select(UserSecurity).where(UserSecurity.user_id == user_id)
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            record = UserSecurity(user_id=user_id, totp_enabled=False)
            self.db.add(record)
            # We don't commit here to allow caller to update fields first
            await self.db.flush() 
            
        return record