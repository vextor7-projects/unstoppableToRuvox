import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from sqlalchemy import update, and_, desc

from app.crud.base import BaseCRUD
from app.models.ledger import (
    InternalLedger,
    DepositTransaction,
    WithdrawalRequest,
)
from app.models.user import User
from app.schemas.exchange import (
    WithdrawalRequestCreate,
    WithdrawalRequestUpdate, # Assuming an update schema for service layer
)
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
    
    Note: Create/Update schemas are BaseModel as entries are created
    internally by services, not directly from API requests.
    """

    async def get_by_transaction_id(
        self, db: AsyncSession, *, transaction_id: str
    ) -> Optional[InternalLedger]:
        """
        Get a ledger entry by its unique transaction_id for idempotency checks.
        """
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
        """
        Get paginated ledger history for a specific user.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_current_balance(
        self, db: AsyncSession, *, user_id: uuid.UUID, token_symbol: str
    ) -> Decimal:
        """
        Get the most recent 'balance_after' for a user and token.
        This provides the current, definitive internal balance.
        """
        stmt = (
            select(self.model.balance_after)
            .filter(
                self.model.user_id == user_id,
                self.model.token_symbol == token_symbol,
            )
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance if balance is not None else Decimal("0")

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
        Atomically creates a new ledger entry.
        This calculates the new balance based on the most recent previous balance.
        
        NOTE: This method commits. For atomic double-entry (transfers),
        the service layer must create two entries and commit manually.
        """
        # Get current balance (this must be done inside the transaction scope,
        # which the service layer will handle, but for single entries this is fine)
        current_balance = await self.get_current_balance(
            db, user_id=user_id, token_symbol=token_symbol
        )
        
        new_balance = current_balance + amount

        if amount < 0 and new_balance < 0:
            # This should be checked in the service layer *before* calling create,
            # but serves as a final database-level safeguard.
            raise ValueError("Insufficient internal balance.")

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
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for DepositTransaction ---

class CRUDDepositTransaction(BaseCRUD[DepositTransaction, BaseModel, BaseModel]):
    """
    CRUD operations for the DepositTransaction model.
    """

    async def get_by_tx_hash(
        self, db: AsyncSession, *, tx_hash: str
    ) -> Optional[DepositTransaction]:
        """
        Get a deposit transaction by its unique on-chain transaction hash.
        """
        stmt = select(self.model).filter(self.model.tx_hash == tx_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_deposits(
        self, db: AsyncSession, *, chain: Chain
    ) -> List[DepositTransaction]:
        """
        Get deposits for a specific chain that are still pending confirmation.
        Used by the deposit monitoring task.
        """
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
        """
        Helper to create a new deposit record, typically when first detected.
        """
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
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for WithdrawalRequest ---

class CRUDWithdrawalRequest(
    BaseCRUD[WithdrawalRequest, WithdrawalRequestCreate, WithdrawalRequestUpdate]
):
    """
    CRUD operations for the WithdrawalRequest model.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: WithdrawalRequestCreate,
        user_id: uuid.UUID,
        priority: int = 0
    ) -> WithdrawalRequest:
        """
        Create a new withdrawal request for a user.
        """
        db_obj = WithdrawalRequest(
            **obj_in.model_dump(),
            user_id=user_id,
            priority=priority,
            status=WithdrawalStatus.PENDING_APPROVAL,
            compliance_check_status=ComplianceCheckStatus.PENDING
        )
        db.add(db_obj)
        await db.commit()
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
        """
        Get paginated withdrawal history for a specific user.
        """
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
        """
        Get a batch of withdrawal requests that are approved and ready
        to be processed (broadcasted) by the withdrawal task.
        
        Fetches highest priority first, then oldest.
        """
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


# Instantiate the CRUD objects for use in the application
crud_ledger = CRUDInternalLedger(InternalLedger)
crud_deposit_transaction = CRUDDepositTransaction(DepositTransaction)
crud_withdrawal_request = CRUDWithdrawalRequest(WithdrawalRequest)