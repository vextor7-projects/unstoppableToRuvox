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
    TransactionStatus, 
    LedgerEntryType, 
    DepositStatus, 
    WithdrawalStatus,
    ComplianceCheckStatus
)


class InternalLedger(Base):
    """
    Represents a single entry in the user's internal (off-chain) balance.
    This is a double-entry-style ledger, though simplified here.
    Positive amounts are credits, negative amounts are debits.
    (Stage 5)
    """
    __tablename__ = "internal_ledger"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # Unique ID for idempotency, can be from the source (e.g., withdrawal_id)
    transaction_id = Column(String(255), unique=True, index=True, nullable=False)
    
    token_symbol = Column(String(20), nullable=False, index=True)
    
    # Amount to credit (positive) or debit (negative)
    amount = Column(Numeric(36, 18), nullable=False)
    
    # The running balance of this token for this user after this entry
    balance_after = Column(Numeric(36, 18), nullable=False)
    
    entry_type = Column(Enum(LedgerEntryType), nullable=False, index=True)
    
    # For internal transfers
    related_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=True,
        index=True
    )
    
    # For linking to on-chain txns (deposits/withdrawals)
    related_tx_hash = Column(String(255), nullable=True, index=True)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.COMPLETED, nullable=False)
    
    # --- Relationships ---
    
    user = relationship("User", back_populates="internal_ledger_entries", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    
    travel_rule_record = relationship("TravelRuleRecord", back_populates="internal_ledger_entry", uselist=False)


class DepositTransaction(Base):
    """
    Tracks on-chain deposits from an external wallet to a company hot wallet,
    to be credited to a user's internal ledger.
    (Stage 5)
    """
    __tablename__ = "deposit_transaction"
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    tx_hash = Column(String(255), unique=True, index=True, nullable=False)
    chain = Column(Enum(Chain), nullable=False)
    
    from_address = Column(String(255), nullable=False, index=True)
    to_address = Column(String(255), nullable=False, index=True) # Our hot wallet
    
    amount = Column(Numeric(36, 18), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    token_address = Column(String(255), nullable=True) # Null for native
    
    confirmations = Column(Integer, default=0, nullable=False)
    status = Column(Enum(DepositStatus), default=DepositStatus.PENDING, nullable=False, index=True)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    credited_at = Column(DateTime(timezone=True), nullable=True) # When ledger is updated
    
    # Link to the ledger entry that credited the user
    internal_ledger_entry_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("internal_ledger.id"), 
        nullable=True
    )

    # --- Relationships ---
    
    user = relationship("User", back_populates="deposits")
    ledger_entry = relationship("InternalLedger")


class WithdrawalRequest(Base):
    """
    Tracks user requests to withdraw funds from their internal ledger
    to an external on-chain address.
    (Stage 5)
    """
    __tablename__ = "withdrawal_request"
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    to_address = Column(String(255), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False)
    
    token_symbol = Column(String(20), nullable=False)
    token_address = Column(String(255), nullable=True) # Null for native
    
    # Amount requested by user
    amount = Column(Numeric(36, 18), nullable=False)
    
    # Network fee deducted
    fee_amount = Column(Numeric(36, 18), nullable=True)
    
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING_APPROVAL, nullable=False, index=True)
    
    priority = Column(Integer, default=0, nullable=False) # For processing queue
    
    compliance_check_status = Column(Enum(ComplianceCheckStatus), default=ComplianceCheckStatus.PENDING, nullable=False)
    compliance_notes = Column(Text, nullable=True)
    
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True) # When broadcasted
    
    # The resulting on-chain transaction hash
    tx_hash = Column(String(255), nullable=True, unique=True, index=True)
    
    # Link to the ledger entry that debited the user
    internal_ledger_entry_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("internal_ledger.id"), 
        nullable=True
    )
    
    # --- Relationships ---
    
    user = relationship("User", back_populates="withdrawals")
    ledger_entry = relationship("InternalLedger")
# Note: User model should have relationships defined as:
# internal_ledger_entries = relationship("InternalLedger", back_populates="user")