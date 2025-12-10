import uuid
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.crud.base import BaseCRUD
from app.models.ledger import (
    InternalLedger,
    DepositTransaction,
    WithdrawalRequest,
)
from app.schemas.exchange import WithdrawalRequestCreate, WithdrawalRequestUpdate
from app.utils.enums import (
    Chain,
    TransactionStatus,
    LedgerEntryType,
    DepositStatus,
    WithdrawalStatus,
    ComplianceCheckStatus,
)

# --- CRUD for InternalLedger ---

class CRUDInternalLedger(BaseCRUD[InternalLedger, BaseModel, BaseModel]):
    """
    CRUD operations for the InternalLedger model.
    Includes Critical Row Locking logic.
    """

    async def get_by_transaction_id(
        self, db: AsyncSession, *, transaction_id: str
    ) -> Optional[InternalLedger]:
        stmt = select(self.model).filter(
            self.model.transaction_id == transaction_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[InternalLedger]:
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_entry(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        transaction_id: str,
        token_symbol: str,
        amount: Decimal,
        entry_type: LedgerEntryType,
        status: TransactionStatus = TransactionStatus.COMPLETED,
        related_user_id: Optional[uuid.UUID] = None,
        related_tx_hash: Optional[str] = None
    ) -> InternalLedger:
        """
        Atomically creates a new ledger entry with ROW LOCKING.
        """
        # 1. LOCK the most recent entry for this user/token.
        # This prevents two concurrent requests from reading the same 'current_balance'
        # and overwriting each other.
        stmt = (
            select(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.token_symbol == token_symbol,
            )
            .order_by(self.model.created_at.desc())
            .limit(1)
            .with_for_update() # <--- CRITICAL PRODUCTION FIX
        )
        result = await db.execute(stmt)
        latest_entry = result.scalar_one_or_none()

        # 2. Calculate New Balance
        current_balance = latest_entry.balance_after if latest_entry else Decimal("0")
        new_balance = current_balance + amount

        # 3. Safety Check (Redundant to Service layer but good for data integrity)
        if new_balance < 0 and amount < 0:
             # In a real double-entry system, we might allow overdrafts for fees,
             # but for a user wallet, this is a hard stop.
             raise ValueError(f"Insufficient funds in ledger lock. Current: {current_balance}")

        # 4. Create Entry
        db_obj = InternalLedger(
            user_id=user_id,
            transaction_id=transaction_id,
            token_symbol=token_symbol,
            amount=amount,
            balance_after=new_balance,
            entry_type=entry_type,
            status=status,
            related_user_id=related_user_id,
            related_tx_hash=related_tx_hash,
        )
        db.add(db_obj)
        
        # 5. Flush only (Service Layer handles Commit)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    # async def get_current_balance(
    #     self, db: AsyncSession, *, user_id: uuid.UUID, token_symbol: str
    # ) -> Decimal:
    #     """
    #     Get the most recent 'balance_after' for a user and token.
    #     This provides the current, definitive internal balance.
    #     """
    #     stmt = (
    #         select(self.model.balance_after)
    #         .filter(
    #             self.model.user_id == user_id,
    #             self.model.token_symbol == token_symbol,
    #         )
    #         .order_by(self.model.created_at.desc())
    #         .limit(1)
    #     )
    #     result = await db.execute(stmt)
    #     balance = result.scalar_one_or_none()
    #     return balance if balance is not None else Decimal("0")


# --- CRUD for DepositTransaction ---

class CRUDDepositTransaction(BaseCRUD[DepositTransaction, BaseModel, BaseModel]):
    async def get_by_tx_hash(
        self, db: AsyncSession, *, tx_hash: str
    ) -> Optional[DepositTransaction]:
        stmt = select(self.model).filter(self.model.tx_hash == tx_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_deposits(
        self, db: AsyncSession, *, chain: Chain
    ) -> List[DepositTransaction]:
        stmt = (
            select(self.model)
            .filter(
                self.model.status == DepositStatus.PENDING,
                self.model.chain == chain
            )
            .order_by(self.model.detected_at)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_deposit(
        self, db: AsyncSession, *, user_id: uuid.UUID, tx_hash: str, 
        chain: Chain, from_address: str, to_address: str, 
        amount: Decimal, token_symbol: str, token_address: Optional[str]
    ) -> DepositTransaction:
        db_obj = DepositTransaction(
            user_id=user_id,
            tx_hash=tx_hash,
            chain=chain,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            token_symbol=token_symbol,
            token_address=token_address,
            status=DepositStatus.PENDING,
            confirmations=0
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for WithdrawalRequest ---

class CRUDWithdrawalRequest(
    BaseCRUD[WithdrawalRequest, WithdrawalRequestCreate, WithdrawalRequestUpdate]
):
    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: WithdrawalRequestCreate,
        user_id: uuid.UUID,
        priority: int = 0
    ) -> WithdrawalRequest:
        db_obj = WithdrawalRequest(
            **obj_in.model_dump(),
            user_id=user_id,
            priority=priority,
            status=WithdrawalStatus.PENDING_APPROVAL,
            compliance_check_status=ComplianceCheckStatus.PENDING
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WithdrawalRequest]:
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.requested_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_pending_for_processing(
        self, db: AsyncSession, limit: int = 100
    ) -> List[WithdrawalRequest]:
        stmt = (
            select(self.model)
            .filter(
                self.model.status == WithdrawalStatus.APPROVED,
                self.model.compliance_check_status == ComplianceCheckStatus.APPROVED
            )
            .order_by(self.model.priority.desc(), self.model.requested_at)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# Instantiate the CRUD objects
crud_ledger = CRUDInternalLedger(InternalLedger)
crud_deposit_transaction = CRUDDepositTransaction(DepositTransaction)
crud_withdrawal_request = CRUDWithdrawalRequest(WithdrawalRequest)