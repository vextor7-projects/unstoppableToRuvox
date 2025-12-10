import uuid
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import Chain, TransactionStatus, TransactionType
from app.schemas.base import IdempotencyMixin

# Reusing Regex from wallet schemas (ideally move to app/utils/validators.py)
EVM_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOLANA_ADDRESS_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
BTC_ADDRESS_REGEX = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$")

class TransactionPrepareRequest(BaseModel):
    """
    Schema for requesting the backend to prepare an on-chain transaction.
    """
    chain: Chain
    from_address: str
    to_address: str
    amount: Decimal = Field(..., gt=0)
    
    token_symbol: Optional[str] = None
    token_address: Optional[str] = None
    fee_level: Optional[str] = Field(None, pattern="^(slow|standard|fast)$")
    data: Optional[str] = None

    @field_validator("from_address", "to_address")
    @classmethod
    def validate_addresses(cls, v: str, info) -> str:
        values = info.data
        chain = values.get("chain")
        if not chain: return v

        if chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            if not EVM_ADDRESS_REGEX.match(v):
                raise ValueError(f"Invalid {chain} address format.")
        elif chain == Chain.SOLANA:
            if not SOLANA_ADDRESS_REGEX.match(v):
                raise ValueError("Invalid Solana address format.")
        elif chain == Chain.BITCOIN:
            if not BTC_ADDRESS_REGEX.match(v):
                raise ValueError("Invalid Bitcoin address format.")
        return v

class FeeEstimate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    token_symbol: str
    usd_value: Optional[Decimal] = Field(None, ge=0)

class TransactionPrepareResponse(BaseModel):
    unsigned_tx: Any
    estimated_fee: FeeEstimate
    simulation_result: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None

class TransactionBroadcastRequest(IdempotencyMixin): # ADDED: Idempotency
    """
    Schema for submitting a signed transaction.
    """
    chain: Chain
    signed_tx: str # Hex or Base64


class TransactionBroadcastResponse(BaseModel):
    tx_hash: str
    message: str = "Transaction broadcasted successfully."


# --- Transaction Status Schemas ---

class TransactionStatusResponse(BaseModel):
    """
    Schema for the response when querying the status of an on-chain transaction.
    """
    tx_hash: str
    status: TransactionStatus
    chain: Chain
    timestamp: Optional[datetime] = None
    block_number: Optional[int] = None
    confirmations: Optional[int] = None
    fee_paid: Optional[FeeEstimate] = None # Actual fee paid, if available
    details: Optional[Dict[str, Any]] = None # Additional chain-specific details