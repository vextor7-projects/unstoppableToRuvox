import uuid
import hmac
import hashlib
from typing import Optional, List

from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.kyc import KycSubmission
from app.models.user import User
from app.schemas.kyc import KycSubmissionCreate, KycSubmissionUpdate
from app.utils.enums import KycStatus, KycLevel, UserStatus
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)

class KycService:
    """
    Service class for managing KYC submissions and user verification levels.
    Integration with external providers (Sumsub/Onfido) would happen here.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_submission(
        self, user_id: uuid.UUID, submission_in: KycSubmissionCreate
    ) -> KycSubmission:
        """
        Create a new KYC submission record.
        In a real implementation, this would call the external KYC provider API
        to generate an SDK token or redirect URL.
        """
        # Check if there is already a pending submission for this level
        stmt = select(KycSubmission).where(
            KycSubmission.user_id == user_id,
            KycSubmission.level == submission_in.level,
            KycSubmission.status == KycStatus.PENDING
        )
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            raise ConflictException(
                detail="A pending submission for this KYC level already exists."
            )

        # Create the submission record
        db_submission = KycSubmission(
            user_id=user_id,
            level=submission_in.level,
            status=KycStatus.PENDING,
            # In a real app, we would store the 'applicantId' from Sumsub here
            external_submission_id=f"ext_{uuid.uuid4().hex[:12]}" 
        )
        
        self.db.add(db_submission)
        await self.db.commit()
        await self.db.refresh(db_submission)
        
        return db_submission

    async def update_submission_status(
        self, submission_id: uuid.UUID, update_in: KycSubmissionUpdate
    ) -> KycSubmission:
        """
        Update the status of a KYC submission (e.g., via Admin or Webhook).
        If approved, it automatically upgrades the user's KYC level.
        """
        stmt = select(KycSubmission).where(KycSubmission.id == submission_id)
        result = await self.db.execute(stmt)
        submission = result.scalars().first()
        
        if not submission:
            raise NotFoundException(detail="KYC submission not found.")
            
        # Update fields
        if update_in.status:
            submission.status = update_in.status
        if update_in.rejection_reason:
            submission.rejection_reason = update_in.rejection_reason
            
        # If approved, upgrade the user
        if update_in.status == KycStatus.APPROVED:
            await self._upgrade_user_kyc_level(submission.user_id, submission.level)
            
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def get_latest_submission(self, user_id: uuid.UUID) -> Optional[KycSubmission]:
        """
        Get the most recent KYC submission for a user.
        """
        stmt = select(KycSubmission).where(
            KycSubmission.user_id == user_id
        ).order_by(desc(KycSubmission.submitted_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def verify_webhook_signature(
        self, signature: str, payload: bytes, secret: str
    ) -> bool:
        """
        Verify the HMAC signature of an incoming webhook from the KYC provider.
        """
        if not secret:
            return False
            
        computed_signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)

    async def _upgrade_user_kyc_level(self, user_id: uuid.UUID, approved_level: KycLevel):
        """
        Internal method to update the User's kyc_level field based on approval.
        It ensures we don't downgrade a user (e.g., Level 3 shouldn't become Level 2).
        """
        # Fetch the user
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return

        # Determine if this is an upgrade
        current_level_value = self._get_level_weight(user.kyc_level)
        new_level_value = self._get_level_weight(approved_level)
        
        if new_level_value > current_level_value:
            user.kyc_level = approved_level
            # If user was restricted/pending verification, we could activate them here
            # if user.status == UserStatus.PENDING: user.status = UserStatus.ACTIVE
            
            self.db.add(user)
            # Commit happens in the calling function (update_submission_status)

    def _get_level_weight(self, level: KycLevel) -> int:
        """
        Helper to compare enum levels numerically.
        """
        weights = {
            KycLevel.NOT_STARTED: 0,
            KycLevel.LEVEL_1: 1, # Email/Phone
            KycLevel.LEVEL_2: 2, # ID Document
            KycLevel.LEVEL_3: 3  # Address Proof
        }
        # Handle potential 'APPROVED_LEVEL_X' mapping if enums differ slightly in models
        # For this project, we assume strict mapping.
        return weights.get(level, 0)