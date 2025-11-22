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
from app.utils.enums import Chain, TransactionStatus, TransactionType


class Portfolio(Base):
    """
    Represents a user's portfolio, which can contain multiple wallets.
    (Stage 1)
    """
    __tablename__ = "portfolio"

    name = Column(String(100), nullable=False)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # --- Relationships ---
    
    user = relationship("User", back_populates="portfolios")
    wallets = relationship(
        "Wallet", 
        back_populates="portfolio", 
        cascade="all, delete-orphan"
    )


class Wallet(Base):
    """
    Represents a single blockchain wallet (address) within a user's portfolio.
    This is for a non-custodial wallet, so it only stores public addresses.
    (Stage 1)
    """
    __tablename__ = "wallet"

    portfolio_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("portfolio.id"), 
        nullable=False, 
        index=True
    )
    chain = Column(Enum(Chain), nullable=False)
    address = Column(String(255), nullable=False, index=True)
    derivation_path = Column(String(255), nullable=True) # e.g., "m/44'/60'/0'/0/0"
    
    # --- Relationships ---
    
    portfolio = relationship("Portfolio", back_populates="wallets")
    
    token_balances = relationship(
        "TokenBalance", 
        back_populates="wallet", 
        cascade="all, delete-orphan"
    )
    
    transactions = relationship(
        "Transaction", 
        back_populates="wallet", 
        cascade="all, delete-orphan"
    )
    
    bitcoin_utxos = relationship(
        "BitcoinUtxo",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'chain', 'address', name='_portfolio_chain_address_uc'),
    )


class TokenBalance(Base):
    """
    Stores the balance of a specific token for a given wallet.
    (Stage 1)
    """
    __tablename__ = "token_balance"

    wallet_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("wallet.id"), 
        nullable=False, 
        index=True
    )
    
    # Coingecko ID for quick price lookups
    token_coingecko_id = Column(String(100), index=True, nullable=True) 
    
    # Null for native currency (e.g., SOL, ETH, BTC)
    token_address = Column(String(255), nullable=True, index=True) 
    token_symbol = Column(String(20), nullable=False)
    
    # Using Numeric for high precision. (e.g., 36 precision, 18 decimal places)
    balance = Column(Numeric(36, 18), default=0.0, nullable=False)
    
    # Store the USD value for quick portfolio overview
    usd_value = Column(Numeric(20, 4), default=0.0, nullable=False)
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- Relationships ---
    
    wallet = relationship("Wallet", back_populates="token_balances")
    
    __table_args__ = (
        UniqueConstraint('wallet_id', 'token_address', name='_wallet_token_uc'),
    )


class Transaction(Base):
    """
    Stores a record of an on-chain transaction related to a user's wallet.
    (Stage 1)
    """
    __tablename__ = "onchain_transaction" # Renamed to avoid 'transaction' keyword

    wallet_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("wallet.id"), 
        nullable=False, 
        index=True
    )
    
    tx_hash = Column(String(255), nullable=False, index=True)
    chain = Column(Enum(Chain), nullable=False)
    
    # e.g., SEND, RECEIVE, SWAP, STAKE, CONTRACT_CALL, PAYMENT
    transaction_type = Column(Enum(TransactionType), nullable=False) 
    
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True) # Can be a contract address
    
    # Amount of the primary token in the transaction
    amount = Column(Numeric(36, 18), nullable=False)
    
    # Primary token address (null for native)
    token_address = Column(String(255), nullable=True) 
    token_symbol = Column(String(20), nullable=True)
    
    fee_amount = Column(Numeric(36, 18), nullable=True)
    
    status = Column(Enum(TransactionStatus), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    block_number = Column(Integer, nullable=True)
    
    # --- Relationships ---
    
    wallet = relationship("Wallet", back_populates="transactions")
    
    __table_args__ = (
        UniqueConstraint('wallet_id', 'tx_hash', name='_wallet_tx_hash_uc'),
    )


class BitcoinUtxo(Base):
    """
    Stores Bitcoin Unspent Transaction Outputs for user's Bitcoin wallets.
    (Stage 1 - Advanced Bitcoin Features)
    """
    __tablename__ = "bitcoin_utxo"
    
    wallet_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("wallet.id"), 
        nullable=False, 
        index=True
    )
    
    tx_hash = Column(String(64), nullable=False, index=True)
    vout = Column(Integer, nullable=False) # Output index
    address = Column(String(255), nullable=False, index=True)
    
    # Amount in Satoshis (as an integer)
    amount_satoshi = Column(Numeric(20, 0), nullable=False) 
    
    script_pub_key = Column(Text, nullable=False)
    is_spent = Column(Boolean, default=False, nullable=False, index=True)
    
    # --- Relationships ---
    
    wallet = relationship("Wallet", back_populates="bitcoin_utxos")
    
    __table_args__ = (
        UniqueConstraint('tx_hash', 'vout', name='_tx_hash_vout_uc'),
    )
