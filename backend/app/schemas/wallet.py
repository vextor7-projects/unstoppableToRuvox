import uuid
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import Chain, TransactionStatus, TransactionType
from app.utils.exceptions import InvalidAddressException

# --- Regex Patterns for Address Validation ---
EVM_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOLANA_ADDRESS_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
# Simple BTC regex (supports Legacy, SegWit, Taproot) - Production apps use lib validation
BTC_ADDRESS_REGEX = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$")

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
    id: uuid.UUID
    wallet_id: uuid.UUID
    last_updated: datetime


# --- Bitcoin UTXO Schema ---

class BitcoinUtxo(BaseModel):
    """
    Schema representing a Bitcoin UTXO (Unspent Transaction Output).
    """
    id: uuid.UUID
    wallet_id: uuid.UUID
    tx_hash: str
    vout: int
    address: str
    amount_satoshi: Decimal
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
    label: str
    chain: Chain
    address: str
    derivation_path: Optional[str] = None

    class Config:
        from_attributes = True

class WalletCreate(WalletBase):
    """
    Schema for creating a wallet via CRUD (Internal).
    Does NOT include portfolio_id as it is passed via parent relationship.
    """
    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str, info) -> str:
        """
        Validate address format based on the selected chain.
        """
        values = info.data
        chain = values.get("chain")
        
        if not chain:
            return v 

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

class WalletAddRequest(BaseModel):
    """
    Schema for adding a PUBLIC wallet address generated on the client.
    NEVER sends mnemonics or private keys.
    """
    portfolio_id: uuid.UUID
    chain: Chain
    address: str
    label: Optional[str] = "Main Wallet"

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str, info) -> str:
        """
        Validate address format based on the selected chain.
        """
        # We need access to the 'chain' field. Pydantic v2 validation logic:
        values = info.data
        chain = values.get("chain")
        
        if not chain:
            return v # Let chain validation fail separately

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

class Wallet(WalletBase):
    """
    Schema representing a complete wallet object returned by the API.
    Includes database-generated ID and user ID.
    """
    id: uuid.UUID
    portfolio_id: uuid.UUID
    token_balances: List[TokenBalance] = []
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
    Schema for updating a portfolio.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class Portfolio(PortfolioBase):
    """
    Schema representing a complete portfolio object returned by the API.
    Includes database-generated ID and user ID.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    wallets: List[Wallet] = []
    total_usd_value: Decimal = Field(Decimal("0.0"), ge=0)


# --- Schemas for Specific API Responses ---

class BalanceResponse(BaseModel):
    """
    Schema for the balance response of a wallet.
    """
    chain: Optional[Chain] = None 
    address: Optional[str] = None 
    total_usd_value: Decimal = Field(..., ge=0)
    balances: List[TokenBalanceBase]


class TransactionBase(BaseModel):
    """
    Base schema for transaction details.
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
    Schema representing a transaction returned by the API.
    """
    id: uuid.UUID
    wallet_id: uuid.UUID

class HistoryResponse(BaseModel):
    """
    Schema for the history response of a wallet.
    """
    transactions: List[Transaction]
    page: int
    limit: int
    total: int