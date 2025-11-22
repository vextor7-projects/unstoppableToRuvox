import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field

from app.utils.enums import Chain, TransactionStatus, TransactionType

# --- Base Transaction Schema (already defined in wallet.py, reuse if needed or redefine) ---
# Assuming TransactionBase and Transaction from wallet.py cover basic display needs.

# --- Transaction Preparation Schemas ---

class TransactionPrepareRequest(BaseModel):
    """
    Schema for requesting the backend to prepare an on-chain transaction.
    This typically involves building the transaction structure and estimating fees.
    """
    chain: Chain
    from_address: str # The sender's public wallet address
    to_address: str   # The recipient's public wallet address or contract address
    amount: Decimal = Field(..., gt=0) # Amount of the token to send
    
    # Specify the token being sent
    token_symbol: Optional[str] = None # e.g., "USDC", null for native currency
    token_address: Optional[str] = None # e.g., SPL or ERC20 address, null for native
    
    # Optional: User preference for transaction speed/fee
    fee_level: Optional[str] = Field(None, pattern="^(slow|standard|fast)$")
    
    # Optional: For EVM chains, could include nonce or gas limits if user wants control
    nonce: Optional[int] = None
    gas_limit: Optional[int] = None
    
    # Optional: For Bitcoin, specific UTXOs to use
    utxos_to_use: Optional[List[Dict[str, Any]]] = None
    
    # Optional: Data for contract interactions
    data: Optional[str] = None

class FeeEstimate(BaseModel):
    """
    Schema representing estimated transaction fee details.
    """
    amount: Decimal = Field(..., ge=0)
    token_symbol: str # e.g., SOL, ETH, MATIC, BTC
    usd_value: Optional[Decimal] = Field(None, ge=0)

class TransactionPrepareResponse(BaseModel):
    """
    Schema for the response after preparing a transaction.
    Contains the data needed by the frontend (and Wallet Core) to sign the transaction.
    """
    # Chain-specific unsigned transaction data (e.g., base64 string for Solana, JSON/dict for EVM/BTC)
    unsigned_tx: Any
    
    # Estimated fee details
    estimated_fee: FeeEstimate
    
    # Optional: Simulation results (e.g., predicted balance changes)
    simulation_result: Optional[Dict[str, Any]] = None
    
    # Optional: Warnings or information (e.g., high fee warning)
    warnings: Optional[List[str]] = None


# --- Transaction Broadcasting Schemas ---

class TransactionBroadcastRequest(BaseModel):
    """
    Schema for submitting a signed transaction to the backend for broadcasting.
    """
    chain: Chain
    # Chain-specific *signed* transaction data (e.g., base64 string, hex string)
    signed_tx: str

class TransactionBroadcastResponse(BaseModel):
    """
    Schema for the response after broadcasting a transaction.
    """
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