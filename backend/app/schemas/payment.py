import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field

from app.utils.enums import Chain, PaymentSessionStatus, TransactionStatus

# --- Payment Session Schemas ---

class PaymentSessionCreateRequest(BaseModel):
    """
    Schema for creating a new payment session (e.g., for QR code generation).
    Typically initiated by a merchant or user wanting to receive payment.
    """
    amount_fiat: Decimal = Field(..., gt=0, description="Amount in fiat currency (e.g., USD)")
    fiat_currency: str = Field("USD", max_length=10, description="Fiat currency code")
    
    # Specify the desired settlement token (defaults to USDC)
    token_symbol: str = Field("USDC", max_length=20, description="Desired settlement token symbol")
    
    # Optional: Link to a specific merchant account if created by a merchant POS
    merchant_id: Optional[uuid.UUID] = None
    
    # Optional: Link to a specific user if created directly by a user
    creator_user_id: Optional[uuid.UUID] = None
    
    # Optional: Client-provided idempotency key
    client_session_id: Optional[str] = Field(None, max_length=100)

class PaymentSessionResponse(BaseModel):
    """
    Schema representing a payment session returned by the API.
    Contains details needed to display QR code or handle NFC.
    """
    id: uuid.UUID
    creator_user_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
    
    amount_fiat: Decimal
    fiat_currency: str
    amount_token: Decimal # Calculated equivalent in settlement token
    token_symbol: str
    
    status: PaymentSessionStatus
    qr_nfc_payload: str # Encrypted data for QR/NFC
    expires_at: datetime
    created_at: datetime
    
    # Link to the transaction once completed
    payment_transaction_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class PaymentExecutionDetails(BaseModel):
    """
    Schema representing details extracted from a scanned QR/NFC payload,
    shown to the payer for confirmation before execution.
    """
    session_id: uuid.UUID
    recipient_display_name: str # Merchant name or user @username
    amount_fiat: Decimal
    fiat_currency: str
    amount_token: Decimal # Amount in settlement token (e.g., USDC)
    token_symbol: str
    expires_at: datetime
    # Optionally include supported chains derived from payload/recipient preferences

# Note: The actual PaymentExecutionRequest might just involve calling an endpoint
# like POST /payments/execute/{session_id} after user authentication,
# potentially including the chosen payment chain/token if multiple options are presented.


# --- Payment Transaction Schemas ---

class PaymentTransactionBase(BaseModel):
    """
    Base schema for representing a completed payment transaction.
    """
    session_id: uuid.UUID
    payer_user_id: Optional[uuid.UUID] = None # Payer might not be our user
    payer_address: str
    recipient_address: str
    tx_hash: str
    chain: Chain
    
    amount_paid: Decimal
    token_paid_symbol: str
    token_paid_address: Optional[str] = None
    
    amount_received: Decimal # Amount in settlement token received by merchant/recipient
    token_received_symbol: str
    
    fee_amount_paid: Optional[Decimal] = None # Network fee paid by payer
    app_fee_amount: Optional[Decimal] = None # App fee collected
    
    timestamp: datetime

    class Config:
        from_attributes = True

class PaymentTransaction(PaymentTransactionBase):
    """
    Full schema for a payment transaction returned by the API.
    """
    id: uuid.UUID


# --- Swap Transaction Schemas (Related to Payments) ---

class SwapTransactionBase(BaseModel):
    """
    Base schema for representing an automatic swap during a payment.
    """
    aggregator: str # e.g., "Jupiter", "1inch"
    token_in_symbol: str
    amount_in: Decimal
    token_out_symbol: str
    amount_out: Decimal

    class Config:
        from_attributes = True

class SwapTransaction(SwapTransactionBase):
    """
    Full schema for a swap transaction related to a payment.
    """
    id: uuid.UUID
    payment_transaction_id: uuid.UUID
    tx_hash: str # Main payment tx hash


# --- Fee Distribution Schemas (Related to Payments) ---

class FeeDistributionBase(BaseModel):
    """
    Base schema for representing fee distribution from a payment.
    """
    app_fee_amount: Decimal
    app_fee_token_symbol: str
    app_fee_recipient_address: str

    class Config:
        from_attributes = True

class FeeDistribution(FeeDistributionBase):
    """
    Full schema for a fee distribution related to a payment.
    """
    id: uuid.UUID
    payment_transaction_id: uuid.UUID
    tx_hash: str # Main payment tx hash

# --- Schemas incorporating related data ---

class PaymentTransactionDetail(PaymentTransaction):
    """
    Detailed payment transaction including optional swap and fee info.
    """
    swap: Optional[SwapTransactionBase] = None
    fee_distribution: Optional[FeeDistributionBase] = None

class PaymentStatusUpdate(BaseModel):
    """
    Schema for WebSocket updates regarding payment session status.
    """
    session_id: uuid.UUID
    status: PaymentSessionStatus
    payment_transaction: Optional[PaymentTransactionDetail] = None # Sent on completion
    error_message: Optional[str] = None # Sent on failure
# --- Note ---
# Additional schemas for deposits and withdrawals would typically be in payment.py,