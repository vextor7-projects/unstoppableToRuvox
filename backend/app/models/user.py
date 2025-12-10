import uuid
from sqlalchemy import (
    Boolean,
    Column,
    String,
    Enum,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base, SoftDeleteMixin
from app.utils.enums import UserRole, KycStatus, UserStatus, Chain



class User(Base, SoftDeleteMixin): # ADDED: SoftDeleteMixin
    __tablename__ = "user_account"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_pin = Column(String(255), nullable=False)
    
    phone_number = Column(String(20), nullable=True)
    
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    kyc_level = Column(Enum(KycStatus), default=KycStatus.NOT_STARTED, nullable=False)
    
    is_superuser = Column(Boolean, default=False)

    # --- Relationships ---
    
    # Security: 1-to-1
    security = relationship("UserSecurity", back_populates="user", uselist=False, cascade="all, delete") # Security can be deleted if user is Hard Deleted
    
    # Wallet: 1-to-many
    # CHANGED: Removed 'delete-orphan' to preserve wallet history even if user is soft-deleted
    portfolios = relationship("Portfolio", back_populates="user")
    
    # KYC: 1-to-many
    kyc_submissions = relationship("KycSubmission", back_populates="user")
    
    # Merchant: 1-to-1
    merchant = relationship("Merchant", back_populates="user", uselist=False)
    
    # Whitelist
    address_whitelist = relationship("AddressWhitelist", back_populates="user")
    
    # Ledger
    internal_ledger_entries = relationship("InternalLedger", back_populates="user", foreign_keys="InternalLedger.user_id")
    
    deposits = relationship("DepositTransaction", back_populates="user")
    withdrawals = relationship("WithdrawalRequest", back_populates="user")
    
    # Compliance
    travel_rule_records = relationship("TravelRuleRecord", back_populates="sender_user")
    blockchain_screenings = relationship("BlockchainScreening", back_populates="user")
    suspicious_activities = relationship("SuspiciousActivity", back_populates="user")
    
    # Staking & VIP
    staking_positions = relationship("StakingPosition", back_populates="user")
    vip_tier = relationship("VipTier", back_populates="user", uselist=False)



    # One-to-Many relationship with PriceAlert
    price_alerts = relationship(
        "PriceAlert",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship with Invoice (as creator)
    invoices = relationship(
        "Invoice",
        back_populates="creator",
        foreign_keys="[Invoice.creator_user_id]"
    )
    
    # One-to-Many relationship with Subscription (as subscriber)
    subscriptions = relationship(
        "Subscription",
        back_populates="subscriber",
        foreign_keys="[Subscription.subscriber_user_id]"
    )
    
    # One-to-Many relationship with PullPaymentApproval (as approver)
    pull_payment_approvals = relationship(
        "PullPaymentApproval",
        back_populates="approver",
        foreign_keys="[PullPaymentApproval.approver_user_id]"
    )


class UserSecurity(Base):
    __tablename__ = "user_security"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), primary_key=True)
    
    totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(1024), nullable=True) # Encrypted
    hashed_backup_codes = Column(String(2048), nullable=True) # Encrypted JSON
    
    user = relationship("User", back_populates="security")


class AddressWhitelist(Base):
    """
    Stores user-approved withdrawal addresses for enhanced security.
    (Stage 18)
    """
    __tablename__ = "address_whitelist"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    
    # --- Relationships ---
    user = relationship("User", back_populates="address_whitelist")

    # --- Constraints ---
    __table_args__ = (
        UniqueConstraint('user_id', 'chain', 'address', name='_user_chain_address_uc'),
    )

