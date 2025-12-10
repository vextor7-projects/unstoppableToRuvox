import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Portfolio, Wallet, TokenBalance, BitcoinUtxo
from app.models.user import User
from app.schemas.wallet import WalletAddRequest
from app.services.blockchain.solana_service import solana_service
from app.services.blockchain.evm_service import evm_service
from app.services.blockchain.bitcoin_service import bitcoin_service
from app.utils.enums import Chain
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException

class WalletService:
    """
    Service for managing user portfolios, wallets, and balances.
    Non-Custodial: We store Public Addresses only.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Portfolio Management ---

    async def create_portfolio(self, user_id: uuid.UUID, name: str) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, name=name)
        self.db.add(portfolio)
        # Using flush instead of commit (Atomic Transaction Rule)
        await self.db.flush()
        await self.db.refresh(portfolio)
        return portfolio

    async def get_user_portfolios(self, user_id: uuid.UUID) -> List[Portfolio]:
        stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_portfolio(self, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Portfolio:
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        result = await self.db.execute(stmt)
        portfolio = result.scalars().first()
        if not portfolio:
            raise NotFoundException("Portfolio not found.")
        return portfolio

    # --- Wallet Creation (Address Registration) ---

    async def register_wallet(self, user_id: uuid.UUID, wallet_in: WalletAddRequest) -> Wallet:
        """
        Register a public address generated on the client side.
        """
        # 1. Verify Portfolio Ownership
        portfolio = await self.get_portfolio(wallet_in.portfolio_id, user_id)

        # 2. Check for Duplicates (Address + Chain) globally or per user?
        # Typically one address per chain per portfolio.
        stmt = select(Wallet).where(
            Wallet.portfolio_id == wallet_in.portfolio_id,
            Wallet.chain == wallet_in.chain,
            Wallet.address == wallet_in.address
        )
        existing = await self.db.execute(stmt)
        if existing.scalars().first():
            raise ConflictException(f"Wallet {wallet_in.address} already exists in this portfolio.")

        # 3. Create Wallet Record
        wallet = Wallet(
            portfolio_id=wallet_in.portfolio_id,
            chain=wallet_in.chain,
            address=wallet_in.address,
            # label=wallet_in.label  (If model has label)
        )
        self.db.add(wallet)
        await self.db.flush()
        await self.db.refresh(wallet)
        
        # 4. Trigger Initial Sync (Optional, async best)
        # We don't await this to keep response fast, or we let client trigger it.
        
        return wallet

    # --- Balance Syncing ---

    async def sync_portfolio_balances(self, portfolio_id: uuid.UUID) -> None:
        stmt = select(Wallet).where(Wallet.portfolio_id == portfolio_id)
        result = await self.db.execute(stmt)
        wallets = result.scalars().all()

        for wallet in wallets:
            await self.sync_wallet_balance(wallet)

    async def sync_wallet_balance(self, wallet: Wallet) -> None:
        try:
            if wallet.chain == Chain.SOLANA:
                sol_bal = await solana_service.get_native_balance(wallet.address)
                await self._update_token_balance(wallet.id, "SOL", sol_bal)
                
                tokens = await solana_service.get_token_accounts(wallet.address)
                for t in tokens:
                    # In prod, fetch symbol from metadata registry using mint.
                    # Fallback to mint address snippet if unknown.
                    symbol = t.get("mint")[:4] 
                    await self._update_token_balance(wallet.id, symbol, t["amount"], t["address"])

            elif wallet.chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
                native_bal = await evm_service.get_native_balance(wallet.chain, wallet.address)
                symbol = "ETH" if wallet.chain != Chain.POLYGON else "MATIC"
                await self._update_token_balance(wallet.id, symbol, native_bal)

            elif wallet.chain == Chain.BITCOIN:
                utxos = await bitcoin_service.get_utxos(wallet.address)
                await self._update_bitcoin_utxos(wallet.id, utxos)
                
                btc_bal = await bitcoin_service.get_balance(wallet.address)
                await self._update_token_balance(wallet.id, "BTC", btc_bal)

        except Exception as e:
            # Log error but don't crash sync loop
            print(f"Failed to sync wallet {wallet.address}: {e}")

    async def _update_token_balance(
        self, wallet_id: uuid.UUID, symbol: str, balance: Decimal, token_addr: str = None
    ) -> None:
        """
        Upsert token balance using Row Locking (via crud_wallet if strictly followed, 
        or direct SQL here for service atomicity).
        """
        # Using a lock to prevent race conditions during sync
        stmt = select(TokenBalance).where(
            TokenBalance.wallet_id == wallet_id,
            TokenBalance.token_symbol == symbol,
            TokenBalance.token_address == token_addr
        ).with_for_update()
        
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if record:
            record.balance = balance
            record.last_updated = datetime.utcnow()
        else:
            record = TokenBalance(
                wallet_id=wallet_id,
                token_symbol=symbol,
                token_address=token_addr,
                balance=balance,
                usd_value=0
            )
            self.db.add(record)
        
        await self.db.flush()

    async def _update_bitcoin_utxos(self, wallet_id: uuid.UUID, utxos: List[Dict]) -> None:
        # 1. Delete old UTXOs
        await self.db.execute(
            delete(BitcoinUtxo).where(BitcoinUtxo.wallet_id == wallet_id)
        )
        # 2. Insert new
        for u in utxos:
            db_utxo = BitcoinUtxo(
                wallet_id=wallet_id,
                tx_hash=u["tx_hash"],
                vout=u["vout"],
                address=u.get("address", ""),
                amount_satoshi=u["value_sats"],
                script_pub_key=u["script_pub_key"],
                is_spent=False
            )
            self.db.add(db_utxo)
        await self.db.flush()