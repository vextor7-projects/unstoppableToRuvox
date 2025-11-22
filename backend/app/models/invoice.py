import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Numeric,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import InvoiceStatus


class Invoice(Base):
    """
    Represents a bill or invoice created by a user (B2B/Freelancer)
    to request payment from another party.
    (Stage 6)
    """
    __tablename__ = "invoice"

    creator_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # Optional email of the person being billed
    payer_email = Column(String(255), nullable=True, index=True)
    
    # The amount due, in fiat (e.g., USD)
    amount_fiat = Column(Numeric(20, 4), nullable=False)
    fiat_currency = Column(String(10), default="USD", nullable=False)
    
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False, index=True)
    
    # A unique, shareable link for this invoice
    payment_link_id = Column(String(50), unique=True, index=True, nullable=False, default=uuid.uuid4)
    
    # The smart contract address this invoice is tied to (if applicable)
    payment_contract_address = Column(String(255), nullable=True)
    
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Link to the payment transaction that settled this invoice
    payment_transaction_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_transaction.id"), 
        nullable=True,
        index=True
    )

    # --- Relationships ---
    
    creator = relationship("User", back_populates="invoices_created")
    
    payment_transaction = relationship("PaymentTransaction")
