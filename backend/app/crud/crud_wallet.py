import uuid
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import update, and_, desc

from app.crud.base import BaseCRUD
from app.models.user import User
from app.models.wallet import (
    Portfolio,
    Wallet,
    TokenBalance,
    Transaction,
    BitcoinUtxo,
)
from app.schemas.wallet import PortfolioCreate, PortfolioUpdate, WalletCreate
from app.utils.enums import Chain, TransactionStatus


class CRUDPortfolio(BaseCRUD[Portfolio, PortfolioCreate, PortfolioUpdate]):
    """
    CRUD operations for Portfolio and its related models:
    Wallet, TokenBalance, Transaction, and BitcoinUtxo.
    """

    # --- Portfolio Methods ---

    async def create_with_user(
        self, db: AsyncSession, *, obj_in: PortfolioCreate, user_id: uuid.UUID
    ) -> Portfolio:
        """
        Create a new portfolio linked to a user.
        """
        db_obj = Portfolio(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> List[Portfolio]:
        """
        Get all portfolios for a specific user.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_with_wallets(
        self, db: AsyncSession, *, id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Portfolio]:
        """
        Get a single portfolio by ID, ensuring it belongs to the user,
        and eagerly load all related wallets and their token balances.
        """
        stmt = (
            select(self.model)
            .filter(self.model.id == id, self.model.user_id == user_id)
            .options(
                selectinload(self.model.wallets).selectinload(Wallet.token_balances)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_wallets(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> List[Portfolio]:
        """
        Get all portfolios for a user, eagerly loading all related
        wallets and their token balances.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .options(
                selectinload(self.model.wallets).selectinload(Wallet.token_balances)
            )
            .order_by(self.model.created_at)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    # --- Wallet Methods ---

    async def create_wallet(
        self, db: AsyncSession, *, obj_in: WalletCreate, portfolio_id: uuid.UUID
    ) -> Wallet:
        """
        Create a new wallet within a specific portfolio.
        """
        db_obj = Wallet(**obj_in.model_dump(), portfolio_id=portfolio_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_wallet(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[Wallet]:
        """
        Get a single wallet by its ID.
        """
        return await db.get(Wallet, id)

    async def get_wallet_by_address(
        self, db: AsyncSession, *, chain: Chain, address: str
    ) -> Optional[Wallet]:
        """
        Get a single wallet by its chain and address.
        """
        stmt = select(Wallet).filter(Wallet.chain == chain, Wallet.address == address)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # --- TokenBalance Methods ---

    async def upsert_token_balance(
        self,
        db: AsyncSession,
        *,
        wallet_id: uuid.UUID,
        token_address: Optional[str],
        token_symbol: str,
        balance: Decimal,
        usd_value: Decimal,
        token_coingecko_id: Optional[str] = None
    ) -> TokenBalance:
        """
        Create or update a token balance for a wallet.
        Uses token_address (or symbol for native) as the unique key per wallet.
        """
        # Find existing balance
        stmt = select(TokenBalance).filter(
            TokenBalance.wallet_id == wallet_id,
            TokenBalance.token_address == token_address,
            TokenBalance.token_symbol == token_symbol,
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if db_obj:
            # Update existing balance
            db_obj.balance = balance
            db_obj.usd_value = usd_value
            if token_coingecko_id:
                db_obj.token_coingecko_id = token_coingecko_id
        else:
            # Create new balance
            db_obj = TokenBalance(
                wallet_id=wallet_id,
                token_address=token_address,
                token_symbol=token_symbol,
                token_coingecko_id=token_coingecko_id,
                balance=balance,
                usd_value=usd_value,
            )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # --- Transaction Methods ---

    async def create_transaction(
        self, db: AsyncSession, *, wallet_id: uuid.UUID, tx_data: Dict[str, Any]
    ) -> Transaction:
        """
        Create a new on-chain transaction record.
        tx_data is a dictionary containing all fields for the Transaction model.
        """
        db_obj = Transaction(wallet_id=wallet_id, **tx_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_transaction_by_hash(
        self, db: AsyncSession, *, wallet_id: uuid.UUID, tx_hash: str
    ) -> Optional[Transaction]:
        """
        Get a specific transaction by its hash, scoped to a wallet.
        """
        stmt = select(Transaction).filter(
            Transaction.wallet_id == wallet_id, Transaction.tx_hash == tx_hash
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_transactions_by_wallet_id(
        self, db: AsyncSession, *, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        Get paginated transaction history for a single wallet.
        """
        stmt = (
            select(Transaction)
            .filter(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    # --- Bitcoin UTXO Methods ---

    async def get_unspent_utxos(
        self, db: AsyncSession, *, wallet_id: uuid.UUID
    ) -> List[BitcoinUtxo]:
        """
        Get all unspent UTXOs for a specific Bitcoin wallet.
        """
        stmt = select(BitcoinUtxo).filter(
            BitcoinUtxo.wallet_id == wallet_id, BitcoinUtxo.is_spent == False
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_utxos_as_spent(
        self, db: AsyncSession, *, wallet_id: uuid.UUID, utxo_tx_hashes: List[str]
    ) -> None:
        """
        Mark a list of UTXOs as spent by their transaction hashes.
        """
        if not utxo_tx_hashes:
            return

        stmt = (
            update(BitcoinUtxo)
            .where(
                BitcoinUtxo.wallet_id == wallet_id,
                BitcoinUtxo.tx_hash.in_(utxo_tx_hashes),
            )
            .values(is_spent=True)
        )
        await db.execute(stmt)
        await db.commit()

    async def create_utxo(
        self, db: AsyncSession, *, wallet_id: uuid.UUID, utxo_data: Dict[str, Any]
    ) -> BitcoinUtxo:
        """
        Create a new Bitcoin UTXO record.
        """
        db_obj = BitcoinUtxo(wallet_id=wallet_id, **utxo_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instantiate the CRUD object for use in the application
crud_wallet = CRUDPortfolio(Portfolio)