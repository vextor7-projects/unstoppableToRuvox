import logging
from asgiref.sync import async_to_sync
from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.subscription import Subscription
from app.services.subscription_service import SubscriptionService
from app.services.ledger_service import LedgerService
from app.utils.enums import SubscriptionStatus
from app.utils.helpers import get_utc_now

logger = logging.getLogger(__name__)

@celery_app.task
def process_due_subscriptions():
    """
    Check for active subscriptions and execute payments atomically.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            sub_service = SubscriptionService(db)
            ledger_service = LedgerService(db)
            now = get_utc_now()
            
            # 1. Find Due Subscriptions
            stmt = select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.next_execution_date <= now
            )
            result = await db.execute(stmt)
            due_subs = result.scalars().all()
            
            logger.info(f"Processing {len(due_subs)} due subscriptions.")
            
            for sub in due_subs:
                try:
                    # ATOMIC BLOCK START
                    # We process one subscription at a time to prevent one failure from blocking others
                    # but ensure payment + schedule update happen together.
                    
                    # 2. Debit User (Creates Withdrawal Request / Internal Transfer)
                    # This adds the Ledger Entry to the session (flushed, not committed)
                    await ledger_service.request_withdrawal(
                        user_id=sub.subscriber_user_id,
                        token_symbol=sub.token_symbol,
                        amount=sub.amount,
                        to_address=sub.recipient_address,
                        chain=sub.chain
                    )
                    
                    # 3. Update Schedule
                    next_date = sub_service._calculate_next_execution(
                        sub.next_execution_date, sub.frequency
                    )
                    sub.last_execution_at = now
                    sub.next_execution_date = next_date
                    db.add(sub)
                    
                    # 4. Commit (Finalize Payment AND Schedule)
                    await db.commit() 
                    logger.info(f"Successfully processed subscription {sub.id}")
                    
                except Exception as e:
                    # Rollback this specific subscription's transaction attempt
                    await db.rollback()
                    logger.error(f"Failed to process subscription {sub.id}: {e}")
                    # Continue to next subscription

    async_to_sync(_run)()