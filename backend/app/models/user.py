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

from app.db.base_class import Base
from app.utils.enums import UserRole, KycStatus, UserStatus, Chain


class User(Base):
    """
    User database model.
    Represents the core user account.
    """
    __tablename__ = "user_account"  # Using 'user_account' to avoid reserved 'user' keyword

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)  # For @username
    phone_number = Column(String(50), unique=True, index=True, nullable=True)
    
    # Hashed PIN (not password, as per mobile-first design)
    hashed_pin = Column(String, nullable=False)
    
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    kyc_level = Column(Enum(KycStatus), default=KycStatus.NOT_VERIFIED, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    
    is_superuser = Column(Boolean, default=False)
    
    # --- Relationships ---

    # One-to-One relationship with UserSecurity
    security = relationship(
        "UserSecurity", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    # One-to-Many relationship with Portfolios
    portfolios = relationship(
        "Portfolio", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship with KycSubmission
    kyc_submissions = relationship(
        "KycSubmission", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship with AddressWhitelist
    address_whitelist = relationship(
        "AddressWhitelist",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship with PriceAlert
    price_alerts = relationship(
        "PriceAlert",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # One-to-Many relationship with InternalLedger
    internal_ledger_entries = relationship(
        "InternalLedger",
        back_populates="user"
        # Not cascade deleting ledger entries on user delete
    )
    
    # One-to-Many relationship with DepositTransaction
    deposits = relationship(
        "DepositTransaction",
        back_populates="user"
    )
    
    # One-to-Many relationship with WithdrawalRequest
    withdrawals = relationship(
        "WithdrawalRequest",
        back_populates="user"
    )
    
    # One-to-Many relationship with StakingPosition
    staking_positions = relationship(
        "StakingPosition",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # One-to-One relationship with VipTier
    vip_tier = relationship(
        "VipTier",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # One-to-One relationship with Merchant
    merchant = relationship(
        "Merchant",
        back_populates="user",
        uselist=False,
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
    """
    Stores sensitive security settings for a user, isolated from the main user table.
    """
    __tablename__ = "user_security"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), primary_key=True)
    
    # Encrypted TOTP secret key
    totp_secret = Column(String, nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    
    # Encrypted JSON list of one-time backup codes
    hashed_backup_codes = Column(String, nullable=True)
    
    # --- Relationships ---
    
    # One-to-One relationship back to User
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

