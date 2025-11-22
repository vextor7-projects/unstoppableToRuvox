import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Numeric,
    UniqueConstraint,
    Text,
    Integer,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import (
    Chain,
    SubscriptionStatus,
    SubscriptionFrequency
)


class Subscription(Base):
    """
    Represents a recurring payment (subscription) set up by a user.
    (Stage 6)
    """
    __tablename__ = "subscription"

    subscriber_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    recipient_address = Column(String(255), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False)
    
    token_symbol = Column(String(20), nullable=False)
    token_address = Column(String(255), nullable=True) # Null for native
    
    # The exact amount to be sent each period
    amount = Column(Numeric(36, 18), nullable=False)
    
    frequency = Column(Enum(SubscriptionFrequency), nullable=False)
    
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)
    
    next_execution_date = Column(DateTime(timezone=True), nullable=False, index=True)
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    
    # The address of the smart contract managing this subscription (if applicable)
    payment_contract_address = Column(String(255), nullable=True)

    # --- Relationships ---
    
    subscriber_user = relationship("User", back_populates="subscriptions")
    

class PullPaymentApproval(Base):
    """
    Represents a user's approval for a specific counterparty (e.g., utility company)
    to "pull" funds up to a certain limit per period.
    (Stage 6)
    """
    __tablename__ = "pull_payment_approval"
    
    approver_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    recipient_address = Column(String(255), nullable=False, index=True) # The party allowed to pull
    chain = Column(Enum(Chain), nullable=False)
    
    token_symbol = Column(String(20), nullable=False)
    token_address = Column(String(255), nullable=True) # Null for native
    
    # The maximum amount that can be pulled per period
    spending_limit = Column(Numeric(36, 18), nullable=False)
    
    frequency = Column(Enum(SubscriptionFrequency), nullable=False) # How often the limit resets
    
    # The amount spent in the current period
    current_period_spent = Column(Numeric(36, 18), nullable=False, default=0)
    
    # When the current spending period ends and resets
    period_end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)

    # --- Relationships ---
    
    approver_user = relationship("User", back_populates="pull_payment_approvals")
