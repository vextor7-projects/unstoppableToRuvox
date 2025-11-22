import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import VipTierLevel

# --- VIP Tier History Schemas ---

class TierHistoryBase(BaseModel):
    """ Base schema for VIP tier change history records. """
    old_tier: Optional[VipTierLevel] = None
    new_tier: VipTierLevel
    reason: Optional[str] = None
    change_date: datetime

    class ConfigDict:
        from_attributes = True

class TierHistory(TierHistoryBase):
    """ Full schema for a VIP tier change history record. """
    id: uuid.UUID
    user_id: uuid.UUID


# --- VIP Benefits Log Schemas ---

class VipBenefitsLogBase(BaseModel):
    """ Base schema for VIP benefit usage logs. """
    benefit_used: str = Field(..., description="Identifier for the benefit used (e.g., 'PRIORITY_WITHDRAWAL')")
    details: Optional[str] = Field(None, description="Additional details about the usage (e.g., amount saved)")
    usage_date: datetime

    class ConfigDict:
        from_attributes = True

class VipBenefitsLog(VipBenefitsLogBase):
    """ Full schema for a VIP benefit usage log record. """
    id: uuid.UUID
    user_id: uuid.UUID


# --- VIP Status Schemas ---

class VipTierBase(BaseModel):
    """ Base schema for user's VIP tier status. """
    tier: VipTierLevel
    monthly_transaction_volume: Decimal = Field(..., description="Current transaction volume (fiat) for the month")
    current_staking_value: Decimal = Field(..., description="Current total staked value (fiat)")
    volume_reset_date: datetime = Field(..., description="Date when the monthly volume counter resets")

    class ConfigDict:
        from_attributes = True

class VipStatusResponse(VipTierBase):
    """
    Schema representing the user's current VIP status, returned by the API.
    Includes user ID and potentially tier requirements/progress.
    """
    user_id: uuid.UUID
    updated_at: datetime
    # Optionally add fields for next tier requirements / progress bar data
    

class VipBenefitsResponse(BaseModel):
    """
    Schema for describing the benefits associated with a specific VIP tier.
    This might be static data or fetched dynamically.
    """
    tier: VipTierLevel
    trading_fee_discount_percent: Optional[Decimal] = None
    priority_withdrawal: bool = False
    dedicated_support: bool = False
    exclusive_staking_apy_boost_percent: Optional[Decimal] = None
    # Add other benefits as defined in requirements
    description: Optional[str] = None