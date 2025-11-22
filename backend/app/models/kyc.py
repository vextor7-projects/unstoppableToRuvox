import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import KycStatus, KycLevel


class KycSubmission(Base):
    """
    KYC Submission database model.
    Stores records of individual KYC attempts for each user,
    linking to an external provider's submission ID.
    (Stage 3 / Stage 10)
    """
    __tablename__ = "kyc_submission"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # ID from the external KYC provider (e.g., Sumsub)
    external_submission_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # The KYC level this submission is for
    level = Column(Enum(KycLevel), nullable=False)
    
    # The current status of this *specific* submission attempt
    status = Column(Enum(KycStatus), default=KycStatus.SUBMITTED, nullable=False)
    
    rejection_reason = Column(Text, nullable=True)  # Reason if status is REJECTED
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True) # Set when approved/rejected
    
    # --- Relationships ---
    
    user = relationship("User", back_populates="kyc_submissions")
