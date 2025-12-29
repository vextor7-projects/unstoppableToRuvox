import uuid
from sqlalchemy import (
    Boolean,
    Column,
    String,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base, SoftDeleteMixin
from app.utils.enums import UserRole, KycStatus, UserStatus, Chain


class User(Base, SoftDeleteMixin):
    __tablename__ = "user_account"

    # Removed unique=True from Column definition to enforce it via Table Args with logic
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    hashed_pin = Column(String(255), nullable=False)
    
    phone_number = Column(String(20), nullable=True)
    
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    kyc_level = Column(Enum(KycStatus), default=KycStatus.NOT_STARTED, nullable=False)
    
    is_superuser = Column(Boolean, default=False)

    # --- Relationships ---
    security = relationship("UserSecurity", back_populates="user", uselist=False, cascade="all, delete") 
    portfolios = relationship("Portfolio", back_populates="user")
    kyc_submissions = relationship("KycSubmission", back_populates="user")
    merchant = relationship("Merchant", back_populates="user", uselist=False)
    address_whitelist = relationship("AddressWhitelist", back_populates="user")
    internal_ledger_entries = relationship("InternalLedger", back_populates="user", foreign_keys="InternalLedger.user_id")
    deposits = relationship("DepositTransaction", back_populates="user")
    withdrawals = relationship("WithdrawalRequest", back_populates="user")
    travel_rule_records = relationship("TravelRuleRecord", back_populates="sender_user")
    blockchain_screenings = relationship("BlockchainScreening", back_populates="user")
    suspicious_activities = relationship("SuspiciousActivity", back_populates="user")
    staking_positions = relationship("StakingPosition", back_populates="user")
    vip_tier = relationship("VipTier", back_populates="user", uselist=False)
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    
    invoices_created = relationship("Invoice", back_populates="creator", foreign_keys="[Invoice.creator_user_id]")
    
    subscriptions = relationship("Subscription", back_populates="subscriber_user", foreign_keys="[Subscription.subscriber_user_id]")
    pull_payment_approvals = relationship("PullPaymentApproval", back_populates="approver_user", foreign_keys="[PullPaymentApproval.approver_user_id]")

    created_payment_sessions = relationship("PaymentSession", back_populates="creator")
    payments_made = relationship("PaymentTransaction", back_populates="payer")

    # --- Constraints ---
    __table_args__ = (
        # Only enforce uniqueness if the user is NOT deleted.
        Index('ix_user_email_active', 'email', unique=True, postgresql_where=(Column('is_deleted') == False)),
        Index('ix_user_username_active', 'username', unique=True, postgresql_where=(Column('is_deleted') == False)),
    )

    

class UserSecurity(Base):
    __tablename__ = "user_security"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), primary_key=True)
    totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(1024), nullable=True) # Encrypted
    hashed_backup_codes = Column(String(2048), nullable=True) # Encrypted JSON
    user = relationship("User", back_populates="security")

class AddressWhitelist(Base):
    __tablename__ = "address_whitelist"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    user = relationship("User", back_populates="address_whitelist")

    __table_args__ = (
        UniqueConstraint('user_id', 'chain', 'address', name='_user_chain_address_uc'),
    )