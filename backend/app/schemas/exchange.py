import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, EmailStr

from app.utils.enums import Chain, LedgerEntryType, DepositStatus, WithdrawalStatus

# --- Internal Ledger Schemas ---

class LedgerEntryBase(BaseModel):
    """
    Base schema for an internal ledger entry.
    """
    token_symbol: str
    amount: Decimal # Positive for credit, negative for debit
    balance_after: Decimal
    entry_type: LedgerEntryType
    related_user_id: Optional[uuid.UUID] = None
    related_tx_hash: Optional[str] = None
    status: str # Should match TransactionStatus or similar

    class Config:
        from_attributes = True

class LedgerEntry(LedgerEntryBase):
    """
    Schema representing a ledger entry returned by the API.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    transaction_id: str # Unique ID for idempotency
    created_at: datetime


# --- Internal Transfer Schemas ---

class InternalTransferRequest(BaseModel):
    """
    Schema for initiating an internal transfer between users.
    """
    recipient_identifier: str = Field(..., description="Recipient's @username or email")
    token_symbol: str
    amount: Decimal = Field(..., gt=0)
    # Optional: idempotency key from client to prevent duplicates
    client_transfer_id: Optional[str] = Field(None, max_length=100)

class InternalTransferResponse(BaseModel):
    """
    Schema for the response after a successful internal transfer.
    """
    sender_ledger_entry: LedgerEntry
    recipient_ledger_entry: LedgerEntry
    message: str = "Transfer successful."


# --- Deposit Schemas ---

class DepositAddressResponse(BaseModel):
    """
    Schema for responding with a user's deposit address for a specific chain.
    """
    chain: Chain
    address: str
    # Optional: Include memo/tag if required by the chain (e.g., XRP, ATOM)
    memo: Optional[str] = None
    qr_code_data: Optional[str] = None # Data to generate QR code


class DepositTransactionBase(BaseModel):
    """
    Base schema for deposit transaction details.
    """
    tx_hash: str
    chain: Chain
    from_address: str
    to_address: str
    amount: Decimal
    token_symbol: str
    token_address: Optional[str] = None
    confirmations: int
    status: DepositStatus
    detected_at: datetime
    credited_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DepositTransaction(DepositTransactionBase):
    """
    Schema representing a deposit transaction record returned by the API.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    internal_ledger_entry_id: Optional[uuid.UUID] = None


# --- Withdrawal Schemas ---

class WithdrawalRequestCreate(BaseModel):
    """
    Schema for requesting a withdrawal from the internal ledger to an on-chain address.
    """
    chain: Chain
    to_address: str
    token_symbol: str
    amount: Decimal = Field(..., gt=0)
    # Optional: 2FA code if required
    totp_code: Optional[str] = Field(None, pattern=r"^\d{6}$")

class WithdrawalRequestBase(BaseModel):
    """
    Base schema for withdrawal request details.
    """
    to_address: str
    chain: Chain
    token_symbol: str
    token_address: Optional[str] = None
    amount: Decimal
    fee_amount: Optional[Decimal] = None
    status: WithdrawalStatus
    tx_hash: Optional[str] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WithdrawalRequest(WithdrawalRequestBase):
    """
    Schema representing a withdrawal request record returned by the API.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    internal_ledger_entry_id: Optional[uuid.UUID] = None


# --- Internal Balance/History Schemas ---

class InternalBalanceResponse(BaseModel):
    """
    Schema for the response when querying a user's internal balance for a token.
    """
    token_symbol: str
    balance: Decimal
    usd_value: Optional[Decimal] = None # Optional: Include USD equivalent


class InternalHistoryResponse(BaseModel):
    """
    Schema for the response when querying internal ledger history. Includes pagination.
    """
    entries: List[LedgerEntry]
    page: int
    limit: int
    total: int


# --- Fiat On-Ramp Webhook Schemas ---

class OnRampWebhookPayload(BaseModel):
    """
    Generic schema for receiving webhook notifications from fiat on-ramp providers
    (like Transak or Ramp). Structure may vary significantly between providers.
    This is a simplified example.
    """
    # Common fields might include:
    event_type: str # e.g., 'ORDER_COMPLETED', 'ORDER_FAILED'
    order_id: str
    user_id: Optional[str] = None # Our internal user ID, if passed during widget init
    wallet_address: Optional[str] = None # Might be our hot wallet or user's internal identifier
    crypto_amount: Optional[Decimal] = None
    crypto_currency: Optional[str] = None # e.g., 'USDC'
    fiat_amount: Optional[Decimal] = None
    fiat_currency: Optional[str] = None # e.g., 'USD'
    transaction_hash: Optional[str] = None # On-chain hash if applicable
    status: str # e.g., 'COMPLETED', 'FAILED'
    # Provider-specific data
    provider_data: Optional[Dict[str, Any]] = None
