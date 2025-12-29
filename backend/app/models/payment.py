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
from app.utils.enums import Chain, PaymentSessionStatus

class PaymentSession(Base):
    __tablename__ = "payment_session"
    
    creator_user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant.user_id"), nullable=True, index=True)
    
    amount_fiat = Column(Numeric(20, 4), nullable=False)
    fiat_currency = Column(String(10), default="USD", nullable=False)
    amount_token = Column(Numeric(36, 18), nullable=False)
    token_symbol = Column(String(20), nullable=False, default="USDC")
    
    status = Column(Enum(PaymentSessionStatus), default=PaymentSessionStatus.PENDING, nullable=False, index=True)
    qr_nfc_payload = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id", use_alter=True, name="fk_payment_session_txn"), 
        nullable=True
    )

    creator = relationship("User", back_populates="created_payment_sessions")
    merchant = relationship("Merchant", back_populates="payment_sessions")
    
    payment_transaction = relationship(
        "PaymentTransaction", 
        foreign_keys=[payment_transaction_id]
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_session.id", use_alter=True, name="fk_payment_txn_session"), 
        nullable=False, 
        index=True
    )
    
    payer_user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True, index=True)
    payer_address = Column(String(255), nullable=False, index=True)
    recipient_address = Column(String(255), nullable=False, index=True)
    
    tx_hash = Column(String(255), unique=True, index=True, nullable=False)
    chain = Column(Enum(Chain), nullable=False)
    
    amount_paid = Column(Numeric(36, 18), nullable=False)
    token_paid_symbol = Column(String(20), nullable=False)
    token_paid_address = Column(String(255), nullable=True)
    
    amount_received = Column(Numeric(36, 18), nullable=False)
    token_received_symbol = Column(String(20), nullable=False)
    
    fee_amount_paid = Column(Numeric(36, 18), nullable=True)
    app_fee_amount = Column(Numeric(36, 18), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Linked internal ledger entry for instant merchant settlement
    internal_ledger_entry_id = Column(UUID(as_uuid=True), ForeignKey("internal_ledger.id"), nullable=True)

    smart_contract_id = Column(UUID(as_uuid=True), ForeignKey("smart_contract.id"), nullable=True)
    
    session = relationship(
        "PaymentSession", 
        foreign_keys=[session_id]
    )
    
    payer = relationship("User", back_populates="payments_made")
    swap = relationship("SwapTransaction", back_populates="payment_transaction", uselist=False)
    fee_distribution = relationship("FeeDistribution", back_populates="payment_transaction", uselist=False)

    smart_contract = relationship("SmartContract", back_populates="payment_transactions")


class SwapTransaction(Base):
    __tablename__ = "swap_transaction"
    
    payment_transaction_id = Column(UUID(as_uuid=True), ForeignKey("payment_transaction.id"), nullable=False, index=True)
    tx_hash = Column(String(255), nullable=False, index=True)
    aggregator = Column(String(50), nullable=False)
    
    token_in_address = Column(String(255), nullable=True)
    token_in_symbol = Column(String(20), nullable=False)
    amount_in = Column(Numeric(36, 18), nullable=False)
    
    token_out_address = Column(String(255), nullable=True)
    token_out_symbol = Column(String(20), nullable=False)
    amount_out = Column(Numeric(36, 18), nullable=False)
    
    payment_transaction = relationship("PaymentTransaction", back_populates="swap")


class FeeDistribution(Base):
    __tablename__ = "fee_distribution"
    
    payment_transaction_id = Column(UUID(as_uuid=True), ForeignKey("payment_transaction.id"), nullable=False, index=True)
    tx_hash = Column(String(255), nullable=False, index=True)
    app_fee_amount = Column(Numeric(36, 18), nullable=False)
    app_fee_token_symbol = Column(String(20), nullable=False)
    app_fee_recipient_address = Column(String(255), nullable=False)
    
    payment_transaction = relationship("PaymentTransaction", back_populates="fee_distribution")