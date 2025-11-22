import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import Chain, TransactionStatus, TransactionType

# --- Token Balance Schemas ---

class TokenBalanceBase(BaseModel):
    """
    Base schema for token balance information.
    """
    token_coingecko_id: Optional[str] = None
    token_address: Optional[str] = None # Null for native currency
    token_symbol: str
    balance: Decimal = Field(..., ge=0)
    usd_value: Decimal = Field(..., ge=0)

    class Config:
        from_attributes = True

class TokenBalance(TokenBalanceBase):
    """
    Schema representing a token balance as returned by the API.
    Includes database ID and last updated timestamp.
    """
    id: uuid.UUID
    wallet_id: uuid.UUID
    last_updated: datetime


# --- Bitcoin UTXO Schema ---

class BitcoinUtxo(BaseModel):
    """
    Schema representing a Bitcoin UTXO.
    """
    id: uuid.UUID
    wallet_id: uuid.UUID
    tx_hash: str
    vout: int
    address: str
    amount_satoshi: Decimal # Represented as Decimal, but value is integer satoshis
    script_pub_key: str
    is_spent: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Wallet Schemas ---

class WalletBase(BaseModel):
    """
    Base schema for wallet information.
    """
    chain: Chain
    address: str
    derivation_path: Optional[str] = None

    class Config:
        from_attributes = True

class WalletCreate(BaseModel):
    """
    Schema for creating a new wallet entry (address) within a portfolio.
    Typically generated internally, not directly via API by user.
    """
    chain: Chain
    address: str
    derivation_path: Optional[str] = None

class Wallet(WalletBase):
    """
    Schema representing a wallet (address) as returned by the API.
    Includes database ID and associated token balances.
    """
    id: uuid.UUID
    portfolio_id: uuid.UUID
    token_balances: List[TokenBalance] = []
    # Optionally include UTXOs if it's a Bitcoin wallet
    bitcoin_utxos: List[BitcoinUtxo] = []


# --- Portfolio Schemas ---

class PortfolioBase(BaseModel):
    """
    Base schema for portfolio information.
    """
    name: str = Field(..., min_length=1, max_length=100)

    class Config:
        from_attributes = True

class PortfolioCreate(PortfolioBase):
    """
    Schema for creating a new portfolio.
    """
    pass

class PortfolioUpdate(BaseModel):
    """
    Schema for updating a portfolio's name.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class Portfolio(PortfolioBase):
    """
    Schema representing a portfolio as returned by the API.
    Includes database ID, user ID, and associated wallets.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    wallets: List[Wallet] = []
    # Optionally add aggregated balance fields
    total_usd_value: Decimal = Field(Decimal("0.0"), ge=0)


# --- Schemas for Specific API Responses ---

class BalanceResponse(BaseModel):
    """
    Schema for the response when querying balances for an address or portfolio.
    """
    chain: Optional[Chain] = None # Included if querying a specific wallet
    address: Optional[str] = None # Included if querying a specific wallet
    total_usd_value: Decimal = Field(..., ge=0)
    balances: List[TokenBalanceBase] # Use base schema for brevity


class TransactionBase(BaseModel):
    """
    Base schema for on-chain transaction details.
    """
    tx_hash: str
    chain: Chain
    transaction_type: TransactionType
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Decimal
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    fee_amount: Optional[Decimal] = None
    status: TransactionStatus
    timestamp: datetime
    block_number: Optional[int] = None

    class Config:
        from_attributes = True

class Transaction(TransactionBase):
    """
    Schema representing an on-chain transaction record returned by the API.
    """
    id: uuid.UUID
    wallet_id: uuid.UUID

class HistoryResponse(BaseModel):
    """
    Schema for the response when querying transaction history. Includes pagination.
    """
    transactions: List[Transaction]
    page: int
    limit: int
    total: int
