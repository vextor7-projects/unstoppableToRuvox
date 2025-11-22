import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.enums import KycLevel, KycStatus

# --- Base Schema ---

class KycSubmissionBase(BaseModel):
    """
    Base schema for KYC submission data.
    """
    level: KycLevel
    # Potentially add fields for uploaded document types/names if needed for creation,
    # but often the external provider handles the details.

    class Config:
        from_attributes = True


# --- Schema for API Input ---

class KycSubmissionCreate(BaseModel):
    """
    Schema used when a user initiates a KYC submission for a specific level.
    The actual document upload might happen via the KYC provider's SDK/widget.
    """
    level: KycLevel
    # May include fields like 'redirect_url' or provider-specific config


# --- Schema for API Input (Admin Update) ---

class KycSubmissionUpdate(BaseModel):
    """
    Schema used by an admin or webhook to update the status of a submission.
    """
    status: KycStatus
    rejection_reason: Optional[str] = None


# --- Schema for API Output ---

class KycSubmission(KycSubmissionBase):
    """
    Schema representing a KYC submission record returned by the API.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    external_submission_id: Optional[str] = None
    status: KycStatus
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


# --- Schema for User's Overall KYC Status ---

class KycStatusResponse(BaseModel):
    """
    Schema representing the user's current overall KYC level and status.
    This might be directly from the User model or derived.
    """
    current_level: KycStatus # Uses the KycStatus enum which includes levels
    # Optional: Include details about the next level or requirements
    next_level_requirements: Optional[str] = None
    class Config:
        from_attributes = True