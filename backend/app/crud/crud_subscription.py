import uuid
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, desc

from app.crud.base import BaseCRUD
from app.utils.helpers import get_utc_now
from app.models.subscription import Subscription, PullPaymentApproval
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    PullPaymentApprovalCreate,
    PullPaymentApprovalUpdate,
)
from app.utils.enums import Chain, SubscriptionStatus, SubscriptionFrequency

# --- CRUD for Subscription (Recurring Payments) ---


class CRUDSubscription(
    BaseCRUD[Subscription, SubscriptionCreate, SubscriptionUpdate]
):
    """
    CRUD operations for the Subscription (recurring payment) model.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: SubscriptionCreate,
        subscriber_user_id: uuid.UUID,
        next_execution_date: datetime
    ) -> Subscription:
        """
        Create a new subscription linked to a user.
        
        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing subscription details.
        :param subscriber_user_id: The UUID of the user creating the subscription.
        :param next_execution_date: The calculated first execution date.
        :return: The newly created Subscription object.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            subscriber_user_id=subscriber_user_id,
            next_execution_date=next_execution_date,
            status=SubscriptionStatus.ACTIVE
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_subscriber(
        self,
        db: AsyncSession,
        *,
        subscriber_user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subscription]:
        """
        Get all subscriptions for a specific user, paginated.
        """
        stmt = (
            select(self.model)
            .filter(self.model.subscriber_user_id == subscriber_user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_due_subscriptions(
        self, db: AsyncSession, *, limit: int = 100
    ) -> List[Subscription]:
        """
        Get a batch of active subscriptions that are due for execution
        (next_execution_date is in the past).
        
        :param db: The asynchronous database session.
        :param limit: The maximum number of subscriptions to fetch.
        :return: A list of due Subscription objects.
        """
        now = get_utc_now()
        stmt = (
            select(self.model)
            .filter(
                self.model.status == SubscriptionStatus.ACTIVE,
                self.model.next_execution_date <= now,
            )
            .order_by(self.model.next_execution_date)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for PullPaymentApproval ---


class CRUDSPullPaymentApproval(
    BaseCRUD[
        PullPaymentApproval,
        PullPaymentApprovalCreate,
        PullPaymentApprovalUpdate,
    ]
):
    """
    CRUD operations for the PullPaymentApproval model.
    """

    async def create_with_approver(
        self,
        db: AsyncSession,
        *,
        obj_in: PullPaymentApprovalCreate,
        approver_user_id: uuid.UUID,
        period_end_date: datetime
    ) -> PullPaymentApproval:
        """
        Create a new pull payment approval linked to a user.
        
        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing approval details.
        :param approver_user_id: The UUID of the user giving the approval.
        :param period_end_date: The calculated end date of the first spending period.
        :return: The newly created PullPaymentApproval object.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            approver_user_id=approver_user_id,
            period_end_date=period_end_date,
            current_period_spent=0,
            status=SubscriptionStatus.ACTIVE
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_approver(
        self,
        db: AsyncSession,
        *,
        approver_user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PullPaymentApproval]:
        """
        Get all pull payment approvals for a specific user, paginated.
        """
        stmt = (
            select(self.model)
            .filter(self.model.approver_user_id == approver_user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_active_approval_for_recipient(
        self,
        db: AsyncSession,
        *,
        approver_user_id: uuid.UUID,
        recipient_address: str,
        chain: Chain,
        token_address: Optional[str]
    ) -> Optional[PullPaymentApproval]:
        """
        Get a specific, active pull payment approval for a given recipient
        and token. Used by the payment service to verify a pull request.
        
        :return: The active PullPaymentApproval object if one exists.
        """
        now = get_utc_now()
        stmt = select(self.model).filter(
            self.model.approver_user_id == approver_user_id,
            self.model.recipient_address == recipient_address,
            self.model.chain == chain,
            self.model.token_address == token_address,
            self.model.status == SubscriptionStatus.ACTIVE,
            self.model.period_end_date > now,  # Ensure period is still valid
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_expired_approvals_for_reset(
        self, db: AsyncSession, *, limit: int = 100
    ) -> List[PullPaymentApproval]:
        """
        Get a batch of active pull payment approvals whose spending period
        has ended and need to be reset.
        
        :return: A list of PullPaymentApproval objects needing a reset.
        """
        now = get_utc_now()
        stmt = (
            select(self.model)
            .filter(
                self.model.status == SubscriptionStatus.ACTIVE,
                self.model.period_end_date <= now,
            )
            .order_by(self.model.period_end_date)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# Instantiate the CRUD objects for use in the application
crud_subscription = CRUDSubscription(Subscription)
crud_pull_payment_approval = CRUDSPullPaymentApproval(PullPaymentApproval)