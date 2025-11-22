import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Numeric,
    Text,
    Integer,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import Chain, VipTierLevel


class StakingPosition(Base):
    """
    Represents an active staking position for a user.
    (Stage 7)
    """
    __tablename__ = "staking_position"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # Symbol of the staked token (e.g., "USDC", "USDT")
    token_symbol = Column(String(20), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False, default=Chain.SOLANA)
    
    amount = Column(Numeric(36, 18), nullable=False)
    
    # The APY (as a percentage, e.g., 5.5) at the time of staking
    apy_at_stake = Column(Numeric(10, 4), nullable=False)
    
    is_compounding = Column(Boolean, default=True, nullable=False)
    
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Address of the DeFi protocol where funds are staked (if applicable)
    protocol_address = Column(String(255), nullable=True)

    # --- Relationships ---
    
    user = relationship("User", back_populates="staking_positions")
    interest_accruals = relationship(
        "InterestAccrual", 
        back_populates="staking_position", 
        cascade="all, delete-orphan",
        order_by="desc(InterestAccrual.created_at)"
    )


class InterestAccrual(Base):
    """
    Logs each time interest is calculated and paid to a staking position.
    (Stage 7)
    """
    __tablename__ = "interest_accrual"

    staking_position_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("staking_position.id"), 
        nullable=False, 
        index=True
    )
    
    amount = Column(Numeric(36, 18), nullable=False)
    
    # The APY (as a percentage) at the time of this accrual
    apy_at_accrual = Column(Numeric(10, 4), nullable=False)
    
    accrual_date = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    
    staking_position = relationship("StakingPosition", back_populates="interest_accruals")


class VipTier(Base):
    """
    Stores the current VIP tier and progress for a user.
    (Stage 7)
    """
    __tablename__ = "vip_tier"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        primary_key=True
    )
    
    tier = Column(Enum(VipTierLevel), default=VipTierLevel.BRONZE, nullable=False, index=True)
    
    # Stored as fiat (e.g., USD)
    monthly_transaction_volume = Column(Numeric(20, 4), default=0, nullable=False)
    
    # Stored as fiat (e.g., USD)
    current_staking_value = Column(Numeric(20, 4), default=0, nullable=False)
    
    # When the monthly volume is next scheduled to reset
    volume_reset_date = Column(DateTime(timezone=True), nullable=False)

    # --- Relationships ---
    
    user = relationship("User", back_populates="vip_tier", uselist=False)
    tier_history = relationship("TierHistory", back_populates="user", cascade="all, delete-orphan", order_by="desc(TierHistory.created_at)")
    benefits_log = relationship("VipBenefitsLog", back_populates="user", cascade="all, delete-orphan", order_by="desc(VipBenefitsLog.created_at)")


class TierHistory(Base):
    """
    Audit log for all changes to a user's VIP tier.
    (Stage 7)
    """
    __tablename__ = "tier_history"
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("vip_tier.user_id"), 
        nullable=False, 
        index=True
    )
    
    old_tier = Column(Enum(VipTierLevel), nullable=True)
    new_tier = Column(Enum(VipTierLevel), nullable=False)
    
    reason = Column(String(255), nullable=True) # e.g., "VOLUME_INCREASED", "STAKING_DECREASED"
    
    change_date = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    
    user = relationship("VipTier", back_populates="tier_history")


class VipBenefitsLog(Base):
    """
    Logs the usage of specific VIP benefits for analytics.
    (Stage 7)
    """
    __tablename__ = "vip_benefits_log"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("vip_tier.user_id"), 
        nullable=False, 
        index=True
    )
    
    benefit_used = Column(String(255), nullable=False) # e.g., "PRIORITY_WITHDRAWAL", "FEE_DISCOUNT"
    
    details = Column(Text, nullable=True) # e.g., "Saved 0.50 USD on trade"
    
    usage_date = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    
    user = relationship("VipTier", back_populates="benefits_log")
