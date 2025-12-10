import uuid
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import InternalLedger, DepositTransaction, WithdrawalRequest
from app.models.user import User
from app.utils.enums import (
    LedgerEntryType, 
    TransactionStatus, 
    DepositStatus, 
    WithdrawalStatus
)
from app.utils.exceptions import (
    InsufficientBalanceException, 
    InternalLedgerException,
    NotFoundException,
    ConflictException
)

class LedgerService:
    """
    Service for managing the internal double-entry ledger.
    This is the core of the Off-Chain Exchange system.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: uuid.UUID, token_symbol: str) -> Decimal:
        """
        Get the current internal balance of a user for a specific token.
        We fetch the latest ledger entry to get the running balance.
        """
        stmt = select(InternalLedger).where(
            InternalLedger.user_id == user_id,
            InternalLedger.token_symbol == token_symbol
        ).order_by(desc(InternalLedger.id)) # Latest entry first
        
        result = await self.db.execute(stmt)
        latest_entry = result.scalars().first()
        
        return latest_entry.balance_after if latest_entry else Decimal(0)

    async def credit_user(
        self, 
        user_id: uuid.UUID, 
        token_symbol: str, 
        amount: Decimal, 
        transaction_id: str, 
        entry_type: LedgerEntryType,
        related_tx_hash: Optional[str] = None,
        related_user_id: Optional[uuid.UUID] = None
    ) -> InternalLedger:
        """
        Add funds to a user's internal balance (CREDIT).
        """
        if amount <= 0:
            raise InternalLedgerException(detail="Credit amount must be positive.")

        # Idempotency Check
        await self._check_idempotency(transaction_id)

        current_balance = await self.get_balance(user_id, token_symbol)
        new_balance = current_balance + amount
        
        entry = InternalLedger(
            user_id=user_id,
            token_symbol=token_symbol,
            amount=amount, # Positive
            balance_after=new_balance,
            transaction_id=transaction_id,
            entry_type=entry_type,
            related_tx_hash=related_tx_hash,
            related_user_id=related_user_id,
            status=TransactionStatus.COMPLETED
        )
        
        self.db.add(entry)
        # We don't commit here to allow caller to wrap in larger transaction
        await self.db.flush() 
        return entry

    async def debit_user(
        self, 
        user_id: uuid.UUID, 
        token_symbol: str, 
        amount: Decimal, 
        transaction_id: str, 
        entry_type: LedgerEntryType,
        related_tx_hash: Optional[str] = None,
        related_user_id: Optional[uuid.UUID] = None,
        allow_overdraft: bool = False
    ) -> InternalLedger:
        """
        Deduct funds from a user's internal balance (DEBIT).
        """
        if amount <= 0:
            raise InternalLedgerException(detail="Debit amount must be positive.")

        # Idempotency Check
        await self._check_idempotency(transaction_id)

        current_balance = await self.get_balance(user_id, token_symbol)
        
        if not allow_overdraft and current_balance < amount:
            raise InsufficientBalanceException(
                detail=f"Insufficient {token_symbol} balance. Available: {current_balance}, Required: {amount}"
            )
            
        new_balance = current_balance - amount
        
        entry = InternalLedger(
            user_id=user_id,
            token_symbol=token_symbol,
            amount=-amount, # Negative for debit
            balance_after=new_balance,
            transaction_id=transaction_id,
            entry_type=entry_type,
            related_tx_hash=related_tx_hash,
            related_user_id=related_user_id,
            status=TransactionStatus.COMPLETED
        )
        
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def process_internal_transfer(
        self, 
        sender_id: uuid.UUID, 
        recipient_identifier: str, 
        token_symbol: str, 
        amount: Decimal
    ) -> tuple[InternalLedger, InternalLedger]:
        """
        Execute an instant transfer between two users (Stage 5).
        """
        # 1. Resolve Recipient
        # We need to import UserService here or execute a direct query to avoid circular imports
        # Direct query is safer for this specific lookup
        stmt = select(User).where(
            (User.username == recipient_identifier) | (User.email == recipient_identifier)
        )
        result = await self.db.execute(stmt)
        recipient = result.scalars().first()
        
        if not recipient:
            raise NotFoundException(detail="Recipient not found.")
            
        if recipient.id == sender_id:
            raise InternalLedgerException(detail="Cannot transfer to self.")

        # 2. Generate Transaction IDs
        tx_base = uuid.uuid4().hex
        sender_tx_id = f"int_send_{tx_base}"
        recipient_tx_id = f"int_recv_{tx_base}"

        # 3. Debit Sender
        debit_entry = await self.debit_user(
            user_id=sender_id,
            token_symbol=token_symbol,
            amount=amount,
            transaction_id=sender_tx_id,
            entry_type=LedgerEntryType.INTERNAL_TRANSFER_SENT,
            related_user_id=recipient.id
        )

        # 4. Credit Recipient
        credit_entry = await self.credit_user(
            user_id=recipient.id,
            token_symbol=token_symbol,
            amount=amount,
            transaction_id=recipient_tx_id,
            entry_type=LedgerEntryType.INTERNAL_TRANSFER_RECEIVED,
            related_user_id=sender_id
        )
        
        await self.db.commit()
        return debit_entry, credit_entry

    async def process_deposit(self, deposit_id: uuid.UUID) -> InternalLedger:
        """
        Finalize an on-chain deposit by crediting the user's ledger.
        Called after sufficient confirmations are reached.
        """
        stmt = select(DepositTransaction).where(DepositTransaction.id == deposit_id)
        result = await self.db.execute(stmt)
        deposit = result.scalars().first()
        
        if not deposit:
            raise NotFoundException(detail="Deposit not found.")
            
        if deposit.status == DepositStatus.COMPLETED:
            raise ConflictException(detail="Deposit already processed.")
            
        # Update Deposit Status
        deposit.status = DepositStatus.COMPLETED
        
        # Credit User
        tx_id = f"dep_{deposit.tx_hash}"
        ledger_entry = await self.credit_user(
            user_id=deposit.user_id,
            token_symbol=deposit.token_symbol,
            amount=deposit.amount,
            transaction_id=tx_id,
            entry_type=LedgerEntryType.DEPOSIT,
            related_tx_hash=deposit.tx_hash
        )
        
        # Link
        deposit.internal_ledger_entry_id = ledger_entry.id
        
        await self.db.commit()
        return ledger_entry

    async def request_withdrawal(
        self, 
        user_id: uuid.UUID, 
        token_symbol: str, 
        amount: Decimal, 
        to_address: str,
        chain: str # Enum
    ) -> WithdrawalRequest:
        """
        Handle a user's request to withdraw funds.
        Immediately debits the ledger (pending status) to prevent double-spend.
        """
        # 1. Create Withdrawal Request Record
        withdrawal = WithdrawalRequest(
            user_id=user_id,
            token_symbol=token_symbol,
            amount=amount,
            to_address=to_address,
            chain=chain,
            status=WithdrawalStatus.PENDING_APPROVAL
        )
        self.db.add(withdrawal)
        await self.db.flush() # Get ID
        
        # 2. Debit User Ledger
        tx_id = f"wd_{withdrawal.id}"
        ledger_entry = await self.debit_user(
            user_id=user_id,
            token_symbol=token_symbol,
            amount=amount,
            transaction_id=tx_id,
            entry_type=LedgerEntryType.WITHDRAWAL
        )
        
        # Link
        withdrawal.internal_ledger_entry_id = ledger_entry.id
        
        await self.db.commit()
        return withdrawal

    # --- Internal Helpers ---

    async def _check_idempotency(self, transaction_id: str):
        """
        Ensure this transaction ID hasn't been processed before.
        """
        stmt = select(InternalLedger).where(InternalLedger.transaction_id == transaction_id)
        result = await self.db.execute(stmt)
        if result.scalars().first():
            raise ConflictException(detail=f"Transaction {transaction_id} already processed.")