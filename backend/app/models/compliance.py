import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Numeric,
    Text,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import (
    Chain,
    ComplianceStatus,
    RiskRating,
    ScreeningAction,
    SuspiciousActivityStatus,
    ReportType,
    ReportStatus
)


class TravelRuleRecord(Base):
    """
    Stores collected sender/recipient information for transactions
    exceeding the Travel Rule threshold (e.g., $3,000).
    (Stage 10)
    """
    __tablename__ = "travel_rule_record"

    # Can be linked to an on-chain transaction or an internal transfer
    onchain_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("onchain_transaction.id"), 
        nullable=True, 
        index=True
    )
    internal_ledger_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("internal_ledger.id"), 
        nullable=True, 
        index=True
    )
    
    sender_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # Encrypted PII for sender and recipient
    sender_pii_encrypted = Column(String(2048), nullable=False)
    recipient_pii_encrypted = Column(String(2048), nullable=False)
    
    destination_vasp = Column(String(255), nullable=True) # Name of the receiving VASP
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING, nullable=False, index=True)

    # --- Relationships ---
    
    sender_user = relationship("User", back_populates="travel_rule_records")
    
    onchain_transaction = relationship("Transaction", back_populates="travel_rule_record")
    
    internal_ledger_entry = relationship("InternalLedger", back_populates="travel_rule_record")


class BlockchainScreening(Base):
    """
    Logs the result of screening a blockchain address (e.g., via Chainalysis).
    (Stage 10)
    """
    __tablename__ = "blockchain_screening"

    address = Column(String(255), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False, index=True)
    
    # The user who triggered this screening (e.g., by depositing or adding to whitelist)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=True, 
        index=True
    )
    
    risk_score = Column(Numeric(10, 4), nullable=True) # e.g., 0-10
    risk_rating = Column(Enum(RiskRating), nullable=False, index=True) # LOW, MEDIUM, HIGH
    
    action_taken = Column(Enum(ScreeningAction), nullable=False, default=ScreeningAction.ALLOWED, index=True)
    
    # JSON blob of raw data from the analytics provider
    provider_response = Column(Text, nullable=True)
    
    screening_date = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    
    user = relationship("User", back_populates="blockchain_screenings")


class SuspiciousActivity(Base):
    """
    Logs detected suspicious activity (e.g., structuring, high-risk country).
    (Stage 10)
    """
    __tablename__ = "suspicious_activity"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    detection_reason = Column(String(255), nullable=False) # e.g., "STRUCTURING", "HIGH_RISK_JURISDICTION"
    details = Column(Text, nullable=True) # e.g., "3 transactions near $10k limit"
    
    status = Column(Enum(SuspiciousActivityStatus), default=SuspiciousActivityStatus.FLAGGED, nullable=False, index=True)
    
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(255), nullable=True) # Admin who reviewed
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    
    user = relationship("User", back_populates="suspicious_activities")


class ComplianceReport(Base):
    """
    Stores generated compliance reports (e.g., SAR, CTR drafts).
    (Stage 10)
    """
    __tablename__ = "compliance_report"
    
    report_type = Column(Enum(ReportType), nullable=False, index=True) # SAR, CTR
    
    # Encrypted JSON or text of the report content
    report_data_encrypted = Column(Text, nullable=False)
    
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False, index=True)
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Link to the user/activity that triggered this report, if applicable
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("suspicious_activity.id"), nullable=True, index=True)

    # --- Relationships ---
    
    user = relationship("User")
    activity = relationship("SuspiciousActivity")


class RegulatorySubmission(Base):
    """
    Audit log of all filings submitted to regulatory bodies.
    (Stage 10)
    """
    __tablename__ = "regulatory_submission"
    
    filing_name = Column(String(255), nullable=False) # e.g., "FinCEN Form 107", "Q4 2025 SAR Batch"
    jurisdiction = Column(String(10), nullable=False, index=True) # e.g., "US", "KR"
    
    # Reference to the batch report, if applicable
    compliance_report_id = Column(UUID(as_uuid=True), ForeignKey("compliance_report.id"), nullable=True, index=True)
    
    status = Column(String(50), default="SUBMITTED", nullable=False) # e.g., "SUBMITTED", "ACCEPTED"
    submission_date = Column(DateTime(timezone=True), server_default=func.now())
    response_date = Column(DateTime(timezone=True), nullable=True)
    confirmation_code = Column(String(255), nullable=True)

    # --- Relationships ---
    
    report = relationship("ComplianceReport")


class MsbLicense(Base):
    """
    Stores details about the company's MSB licenses or registrations.
    (Stage 10)
    """
    __tablename__ = "msb_license"

    jurisdiction = Column(String(50), nullable=False, index=True) # e.g., "US_FINCEN", "US_NY"
    license_number = Column(String(100), unique=True, nullable=False)
    
    status = Column(String(50), default="ACTIVE", nullable=False)
    
    issued_date = Column(DateTime(timezone=True), nullable=False)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    renewal_due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Encrypted link to the license document in S3
    document_s3_key = Column(String(1024), nullable=True)

