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
    PaymentSessionStatus, 
    PaymentType,
    TransactionType
)


class PaymentSession(Base):
    """
    Represents a QR code or NFC payment session created by a merchant or user.
    This session is non-custodial and will be fulfilled via a smart contract.
    (Stage 8)
    """
    __tablename__ = "payment_session"
    
    # Can be a user or a merchant
    creator_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=True, 
        index=True
    )
    
    merchant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("merchant.id"), 
        nullable=True, 
        index=True
    )
    
    # Amount in USD (or other fiat)
    amount_fiat = Column(Numeric(20, 4), nullable=False)
    fiat_currency = Column(String(10), default="USD", nullable=False)
    
    # Equivalent amount in the requested settlement token (e.g., USDC)
    amount_token = Column(Numeric(36, 18), nullable=False)
    token_symbol = Column(String(20), nullable=False, default="USDC")
    
    status = Column(Enum(PaymentSessionStatus), default=PaymentSessionStatus.PENDING, nullable=False, index=True)
    
    # Encrypted payload containing merchant signature, amount, expiry, etc.
    qr_nfc_payload = Column(Text, nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Link to the final payment transaction once completed
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id"), 
        nullable=True
    )

    # --- Relationships ---
    
    creator = relationship("User", back_populates="created_payment_sessions")
    merchant = relationship("Merchant", back_populates="payment_sessions")
    payment_transaction = relationship("PaymentTransaction", back_populates="session")


class PaymentTransaction(Base):
    """
    Records a completed payment, linking the on-chain transaction
    to the payment session it fulfilled.
    (Stage 2 / Stage 8)
    """
    __tablename__ = "payment_transaction"
    
    # The session this payment is for. Made nullable to allow for non-session payments?
    # No, should be required.
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_session.id"), 
        nullable=False, 
        index=True
    )
    
    payer_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=True, 
        index=True
    )
    payer_address = Column(String(255), nullable=False, index=True)
    
    recipient_address = Column(String(255), nullable=False, index=True) # Merchant's wallet
    
    tx_hash = Column(String(255), unique=True, index=True, nullable=False)
    chain = Column(Enum(Chain), nullable=False)
    
    # The token and amount the payer actually sent (e.g., SOL, BONK)
    amount_paid = Column(Numeric(36, 18), nullable=False)
    token_paid_symbol = Column(String(20), nullable=False)
    token_paid_address = Column(String(255), nullable=True) # Null for native
    
    # The token and amount the merchant received (e.g., USDC)
    amount_received = Column(Numeric(36, 18), nullable=False)
    token_received_symbol = Column(String(20), nullable=False)
    
    # Fee paid by the payer, in the token they paid with
    fee_amount_paid = Column(Numeric(36, 18), nullable=True)
    
    # App fee distributed from the smart contract
    app_fee_amount = Column(Numeric(36, 18), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # --- Relationships ---
    
    session = relationship("PaymentSession", back_populates="payment_transaction")
    payer = relationship("User", back_populates="payments_made")
    swap = relationship("SwapTransaction", back_populates="payment_transaction", uselist=False)
    fee_distribution = relationship("FeeDistribution", back_populates="payment_transaction", uselist=False)


class SwapTransaction(Base):
    """
    Logs an automatic token swap performed by a payment smart contract
    (e.g., via Jupiter or 1inch).
    (Stage 2)
    """
    __tablename__ = "swap_transaction"
    
    # The payment this swap was for
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id"), 
        nullable=False, 
        index=True
    )
    
    tx_hash = Column(String(255), nullable=False, index=True) # The main payment tx hash
    
    aggregator = Column(String(50), nullable=False) # e.g., "Jupiter", "1inch"
    
    token_in_address = Column(String(255), nullable=True) # Null for native
    token_in_symbol = Column(String(20), nullable=False)
    amount_in = Column(Numeric(36, 18), nullable=False)
    
    token_out_address = Column(String(255), nullable=True) # Null for native
    token_out_symbol = Column(String(20), nullable=False)
    amount_out = Column(Numeric(36, 18), nullable=False)
    
    # --- Relationships ---
    
    payment_transaction = relationship("PaymentTransaction", back_populates="swap")


class FeeDistribution(Base):
    """
    Logs the fee distribution from a payment smart contract.
    (Stage 2)
    """
    __tablename__ = "fee_distribution"
    
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id"), 
        nullable=False, 
        index=True
    )
    
    tx_hash = Column(String(255), nullable=False, index=True) # The main payment tx hash
    
    app_fee_amount = Column(Numeric(36, 18), nullable=False)
    app_fee_token_symbol = Column(String(20), nullable=False)
    app_fee_recipient_address = Column(String(255), nullable=False)
    
    # --- Relationships ---
    
    payment_transaction = relationship("PaymentTransaction", back_populates="fee_distribution")
