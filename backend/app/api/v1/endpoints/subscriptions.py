from typing import Any, List, Dict
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user, get_current_merchant_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionUpdate, 
    Subscription,
    PullPaymentApprovalCreate,
    PullPaymentApprovalUpdate,
    PullPaymentApproval
)
from app.services.subscription_service import SubscriptionService
from app.utils.exceptions import BadRequestException, NotFoundException

router = APIRouter()

# --- Push Subscriptions (User sends money) ---

@router.post("/", response_model=Subscription, status_code=status.HTTP_201_CREATED)
async def create_push_subscription(
    sub_in: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a recurring push subscription.
    The system will attempt to execute this on schedule.
    """
    service = SubscriptionService(db)
    return await service.create_subscription(current_user.id, sub_in)

@router.get("/", response_model=List[Subscription])
async def get_my_subscriptions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List active subscriptions.
    """
    service = SubscriptionService(db)
    return await service.get_user_subscriptions(current_user.id)

@router.patch("/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: uuid.UUID,
    update_in: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Pause or Cancel a subscription.
    """
    service = SubscriptionService(db)
    try:
        return await service.update_subscription(subscription_id, current_user.id, update_in)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Subscription not found.")

# --- Pull Approvals (Merchant pulls money) ---

@router.post("/approvals", response_model=PullPaymentApproval, status_code=status.HTTP_201_CREATED)
async def create_pull_approval(
    approval_in: PullPaymentApprovalCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Grant a merchant permission to pull funds from your account.
    """
    service = SubscriptionService(db)
    return await service.create_pull_approval(current_user.id, approval_in)

@router.post("/approvals/{approval_id}/consume", status_code=status.HTTP_200_OK)
async def execute_pull_payment(
    approval_id: uuid.UUID,
    amount: Decimal,
    current_merchant: User = Depends(get_current_merchant_user), # Only merchants can pull
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Execute a pull payment.
    The authenticated user must be the merchant/recipient defined in the approval.
    """
    service = SubscriptionService(db)
    try:
        return await service.execute_pull_payment(
            merchant_user_id=current_merchant.id,
            approval_id=approval_id,
            amount=amount
        )
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=e.detail)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Approval not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))