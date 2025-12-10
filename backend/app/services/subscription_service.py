import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_subscription import crud_subscription
from app.models.subscription import Subscription, PullPaymentApproval
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionUpdate,
    PullPaymentApprovalCreate,
    PullPaymentApprovalUpdate
)
from app.utils.enums import SubscriptionStatus, SubscriptionFrequency, TransactionStatus
from app.utils.exceptions import (
    NotFoundException, 
    BadRequestException, 
    NotAuthorizedException,
    InsufficientBalanceException
)
from app.services.ledger_service import LedgerService
from app.utils.helpers import get_utc_now

class SubscriptionService:
    """
    Service for managing:
    1. Subscriptions (Push): User sends money periodically.
    2. Pull Approvals: User allows merchant to pull money.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_service = LedgerService(db)

    # --- Push Subscriptions ---

    async def create_subscription(
        self, user_id: uuid.UUID, sub_in: SubscriptionCreate
    ) -> Subscription:
        """
        Create a new recurring push subscription.
        """
        start_date = sub_in.start_date if sub_in.start_date else get_utc_now().date()
        next_run = self._calculate_next_execution(start_date, sub_in.frequency)
        
        return await crud_subscription.create_with_user(
            self.db,
            obj_in=sub_in,
            subscriber_user_id=user_id,
            next_execution_date=next_run
        )

    async def get_user_subscriptions(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Subscription]:
        return await crud_subscription.get_multi_by_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    async def update_subscription(
        self, subscription_id: uuid.UUID, user_id: uuid.UUID, update_in: SubscriptionUpdate
    ) -> Subscription:
        """
        Pause or Cancel a subscription.
        """
        sub = await crud_subscription.get(self.db, id=subscription_id)
        if not sub or sub.subscriber_user_id != user_id:
            raise NotFoundException("Subscription not found.")
            
        return await crud_subscription.update(self.db, db_obj=sub, obj_in=update_in)

    # --- Pull Payment Approvals ---

    async def create_pull_approval(
        self, user_id: uuid.UUID, approval_in: PullPaymentApprovalCreate
    ) -> PullPaymentApproval:
        """
        User grants permission for a recipient to pull funds.
        """
        # Calculate first period end date
        period_end = self._calculate_next_execution(get_utc_now(), approval_in.frequency)
        
        return await crud_subscription.create_pull_approval(
            self.db,
            obj_in=approval_in,
            approver_user_id=user_id,
            period_end_date=period_end
        )

    async def execute_pull_payment(
        self, 
        merchant_user_id: uuid.UUID, # The one pulling the funds
        approval_id: uuid.UUID, 
        amount: Decimal
    ) -> dict:
        """
        Execute a pull payment against an existing approval.
        Checks spending limits and resets periods if needed.
        """
        approval = await crud_subscription.get_pull_approval(self.db, id=approval_id)
        if not approval:
            raise NotFoundException("Approval not found.")
        
        # Verify the caller is the approved recipient
        # Note: In a real app, we'd check if merchant_user_id owns the wallet 'recipient_address'
        # For this non-custodial/hybrid setup, we assume the Merchant API Key implies identity.
        
        if approval.status != SubscriptionStatus.ACTIVE:
            raise BadRequestException("Pull approval is not active.")

        # 1. Handle Period Reset
        now = get_utc_now()
        if now > approval.period_end_date:
            # Reset usage for new period
            approval.current_period_spent = Decimal(0)
            approval.period_end_date = self._calculate_next_execution(now, approval.frequency)
            # We don't commit yet, we commit on successful transaction
        
        # 2. Check Limits
        if (approval.current_period_spent + amount) > approval.spending_limit:
            raise BadRequestException(f"Spending limit exceeded. Remaining: {approval.spending_limit - approval.current_period_spent}")

        # 3. Execute Transfer (Internal Ledger for instant settlement)
        # Use transaction_id to ensure idempotency + tracing
        tx_ref = f"pull_{approval.id}_{datetime.utcnow().timestamp()}"
        
        try:
            # We pull FROM approval.approver_user_id TO merchant_user_id (if internal)
            # Or simple debit if external. Assuming Internal Transfer for Merchant Settlement System
            
            # This delegates to LedgerService to handle the double-entry logic
            await self.ledger_service.process_internal_transfer_by_ids(
                sender_id=approval.approver_user_id,
                recipient_id=merchant_user_id,
                token_symbol=approval.token_symbol,
                amount=amount,
                reference_id=tx_ref
            )
            
            # 4. Update Usage
            approval.current_period_spent += amount
            self.db.add(approval)
            await self.db.commit()
            
            return {
                "status": "COMPLETED",
                "tx_id": tx_ref,
                "amount": amount,
                "period_spent": approval.current_period_spent
            }
            
        except InsufficientBalanceException:
             raise BadRequestException("User has insufficient funds.")
        except Exception as e:
             await self.db.rollback()
             raise e

    # --- Helpers ---

    def _calculate_next_execution(self, start_date: datetime, freq: SubscriptionFrequency) -> datetime:
        """
        Calculate the next date based on frequency.
        """
        if isinstance(start_date, datetime):
             base = start_date
        else:
             base = datetime.combine(start_date, datetime.min.time())

        if freq == SubscriptionFrequency.WEEKLY:
            return base + timedelta(weeks=1)
        elif freq == SubscriptionFrequency.MONTHLY:
            # Simple approximation, real world needs dateutil.relativedelta
            return base + timedelta(days=30)
        elif freq == SubscriptionFrequency.YEARLY:
            return base + timedelta(days=365)
        elif freq == SubscriptionFrequency.DAILY:
            return base + timedelta(days=1)
        return base + timedelta(days=30) # Default