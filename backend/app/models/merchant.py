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
    KycStatus,
    SettlementStatus,
    SettlementFrequency,
    MerchantEmployeeRole
)


class Merchant(Base):
    """
    Represents a merchant account, linked one-to-one with a user account.
    (Stage 9)
    """
    __tablename__ = "merchant"

    # User ID is both the PK and FK to user_account
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        primary_key=True
    )
    
    # We add a separate ID column (optional but often safer for ORMs) 
    # OR we stick to user_id as PK. Since you already used user_id as PK,
    # let's keep it but ensure Alembic sees it as the reference target.
    
    business_name = Column(String(255), nullable=False, index=True)
    business_type = Column(String(100), nullable=True)
    registration_number = Column(String(100), nullable=True, index=True)
    business_address = Column(Text, nullable=True)
    
    kyc_status = Column(Enum(KycStatus), default=KycStatus.NOT_STARTED, nullable=False, index=True)
    
    # Settlement preferences
    settlement_frequency = Column(
        Enum(SettlementFrequency), 
        default=SettlementFrequency.DAILY, 
        nullable=False
    )
    settlement_wallet_address = Column(String(255), nullable=True)
    settlement_chain = Column(Enum(Chain), nullable=True)
    settlement_token_symbol = Column(String(20), default="USDC", nullable=True)

    # --- Relationships ---
    
    # One-to-One with User
    user = relationship("User", back_populates="merchant", uselist=False)
    
    # One-to-One with MerchantKyc
    kyc_submission = relationship("MerchantKyc", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    
    # One-to-Many with MerchantSettlement
    settlements = relationship("MerchantSettlement", back_populates="merchant", order_by="desc(MerchantSettlement.created_at)")
    
    # One-to-Many with MerchantEmployee
    employees = relationship("MerchantEmployee", back_populates="merchant", cascade="all, delete-orphan")
    
    # One-to-Many with MerchantTerminal
    terminals = relationship("MerchantTerminal", back_populates="merchant", cascade="all, delete-orphan")
    
    # One-to-Many with PaymentSession (sessions created by this merchant)
    payment_sessions = relationship("PaymentSession", back_populates="merchant")


class MerchantKyc(Base):
    """
    Stores business-specific KYC documents and status for a merchant.
    (Stage 9)
    """
    __tablename__ = "merchant_kyc"
    
    merchant_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant.user_id"), 
        primary_key=True
    )
    
    document_type = Column(String(100), nullable=False) # e.g., "BUSINESS_REGISTRATION"
    
    # Reference to the encrypted file in S3
    document_s3_key = Column(String(1024), nullable=False) 
    address_proof_s3_key = Column(String(1024), nullable=True)
    
    status = Column(Enum(KycStatus), default=KycStatus.PENDING, nullable=False, index=True)
    
    review_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    
    merchant = relationship("Merchant", back_populates="kyc_submission")


class MerchantSettlement(Base):
    """
    Represents a batch settlement for a merchant (e.g., daily payout).
    (Stage 9)
    """
    __tablename__ = "merchant_settlement"

    merchant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant.user_id"), 
        nullable=False, 
        index=True
    )
    
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    total_volume_fiat = Column(Numeric(20, 4), nullable=False)
    total_fee_fiat = Column(Numeric(20, 4), nullable=False)
    settlement_amount_fiat = Column(Numeric(20, 4), nullable=False)
    
    settlement_token_symbol = Column(String(20), nullable=False)
    settlement_token_amount = Column(Numeric(36, 18), nullable=False)
    
    settlement_wallet_address = Column(String(255), nullable=False)
    settlement_chain = Column(Enum(Chain), nullable=False)
    
    status = Column(Enum(SettlementStatus), default=SettlementStatus.PENDING, nullable=False, index=True)
    
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # The on-chain transaction hash for the settlement payout
    tx_hash = Column(String(255), nullable=True, index=True)

    # --- Relationships ---
    
    merchant = relationship("Merchant", back_populates="settlements")
    details = relationship("SettlementDetail", back_populates="settlement", cascade="all, delete-orphan")


class SettlementDetail(Base):
    """
    A link table connecting a settlement batch to the individual
    payment transactions it includes.
    (Stage 9)
    """
    __tablename__ = "settlement_detail"
    
    settlement_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant_settlement.id"), 
        primary_key=True
    )
    
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id"), 
        primary_key=True, 
        unique=True
    )

    # --- Relationships ---
    
    settlement = relationship("MerchantSettlement", back_populates="details")
    payment_transaction = relationship("PaymentTransaction", uselist=False)


class MerchantEmployee(Base):
    """
    Represents an employee account created by a merchant, with limited permissions.
    (Stage 9)
    """
    __tablename__ = "merchant_employee"
    
    merchant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant.user_id"), 
        nullable=False, 
        index=True
    )
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(MerchantEmployeeRole), default=MerchantEmployeeRole.CASHIER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    
    merchant = relationship("Merchant", back_populates="employees")


class MerchantTerminal(Base):
    """
    Represents a single "Point of Sale" terminal (virtual or physical)
    for a merchant, with its own API key for creating payment sessions.
    (Stage 9)
    """
    __tablename__ = "merchant_terminal"

    merchant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant.user_id"), 
        nullable=False, 
        index=True
    )
    
    terminal_name = Column(String(100), nullable=False)
    
    # Hashed API key for authentication
    hashed_api_key = Column(String(255), unique=True, index=True, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    
    merchant = relationship("Merchant", back_populates="terminals")