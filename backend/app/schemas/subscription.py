import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.enums import Chain, SubscriptionStatus, SubscriptionFrequency

# --- Subscription (Recurring Payment) Schemas ---

class SubscriptionBase(BaseModel):
    """
    Base schema containing common fields for a recurring payment subscription.
    """
    recipient_address: str = Field(..., description="Blockchain address of the recipient")
    chain: Chain = Field(..., description="Blockchain network for the subscription")
    token_symbol: str = Field(..., max_length=20, description="Symbol of the token to be sent")
    token_address: Optional[str] = Field(None, description="Address of the token (null for native currency)")
    amount: Decimal = Field(..., gt=0, description="Amount of token to send each period")
    frequency: SubscriptionFrequency = Field(..., description="How often the payment should occur (e.g., MONTHLY)")
    
    # Optional: Start date for the subscription (defaults to immediate if not provided)
    start_date: Optional[date] = Field(None, description="Date the subscription should start")

    class Config:
        from_attributes = True


class SubscriptionCreate(SubscriptionBase):
    """
    Schema used when creating a new subscription via the API.
    subscriber_user_id will be derived from the authenticated user context.
    next_execution_date will be calculated based on start_date/frequency.
    """
    pass # Inherits fields from SubscriptionBase


class SubscriptionUpdate(BaseModel):
    """
    Schema for updating an existing subscription.
    Typically only status (pause/cancel) might be allowed.
    Changing amount/frequency might require creating a new subscription.
    """
    status: Optional[SubscriptionStatus] = Field(None, description="New status (e.g., PAUSED, CANCELLED)")
    # Potentially allow updates to other fields if business logic permits
    # amount: Optional[Decimal] = None
    # frequency: Optional[SubscriptionFrequency] = None


class Subscription(SubscriptionBase):
    """
    Schema representing a complete subscription object returned by the API.
    Includes database-generated fields.
    """
    id: uuid.UUID
    subscriber_user_id: uuid.UUID
    status: SubscriptionStatus
    next_execution_date: datetime
    last_execution_at: Optional[datetime] = None
    payment_contract_address: Optional[str] = None # If managed by a smart contract
    created_at: datetime
    updated_at: datetime


# --- Pull Payment Approval Schemas ---

class PullPaymentApprovalBase(BaseModel):
    """
    Base schema containing common fields for a pull payment approval.
    """
    recipient_address: str = Field(..., description="Address allowed to pull funds")
    chain: Chain = Field(..., description="Blockchain network for the approval")
    token_symbol: str = Field(..., max_length=20, description="Symbol of the token allowed")
    token_address: Optional[str] = Field(None, description="Address of the token (null for native)")
    spending_limit: Decimal = Field(..., gt=0, description="Maximum amount allowed per period")
    frequency: SubscriptionFrequency = Field(..., description="How often the spending limit resets")

    class Config:
        from_attributes = True


class PullPaymentApprovalCreate(PullPaymentApprovalBase):
    """
    Schema used when creating a new pull payment approval via the API.
    approver_user_id derived from auth context.
    period_end_date calculated based on frequency.
    """
    pass # Inherits fields from PullPaymentApprovalBase


class PullPaymentApprovalUpdate(BaseModel):
    """
    Schema for updating an existing pull payment approval.
    Allows changing status (pause/revoke) or the spending limit.
    """
    status: Optional[SubscriptionStatus] = Field(None, description="New status (e.g., PAUSED, REVOKED)")
    spending_limit: Optional[Decimal] = Field(None, gt=0, description="New spending limit per period")


class PullPaymentApproval(PullPaymentApprovalBase):
    """
    Schema representing a complete pull payment approval object returned by the API.
    Includes database-generated fields.
    """
    id: uuid.UUID
    approver_user_id: uuid.UUID
    current_period_spent: Decimal = Field(..., description="Amount spent in the current period")
    period_end_date: datetime = Field(..., description="When the current spending period ends")
    status: SubscriptionStatus # Uses SubscriptionStatus enum (ACTIVE, PAUSED, REVOKED)
    created_at: datetime
    updated_at: datetime
