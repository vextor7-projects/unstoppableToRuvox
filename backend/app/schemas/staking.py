import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import Chain

# --- Staking Option Schema ---

class StakingOption(BaseModel):
    """
    Schema representing an available staking option (e.g., USDC on Solana).
    This data might be fetched dynamically or configured.
    """
    token_symbol: str = Field(..., description="Symbol of the token that can be staked (e.g., 'USDC')")
    chain: Chain = Field(..., description="The blockchain network for this staking option")
    apy_percentage: Decimal = Field(..., description="Current estimated Annual Percentage Yield (e.g., 5.5 for 5.5%)")
    minimum_amount: Decimal = Field(0, description="Minimum amount required to stake")
    # Add other relevant details like lock-up period (if any), provider, etc.
    provider: Optional[str] = Field(None, description="Name of the underlying DeFi protocol or provider")
    supports_compounding: bool = Field(True, description="Whether auto-compounding is supported")


# --- Staking Request Schemas ---

class StakeRequest(BaseModel):
    """
    Schema used when a user initiates a staking action.
    """
    token_symbol: str = Field(..., description="Symbol of the token to stake")
    chain: Chain = Field(..., description="Network for staking")
    amount: Decimal = Field(..., gt=0, description="Amount of the token to stake")
    # Option to disable auto-compounding if supported
    enable_compounding: bool = Field(True, description="Enable automatic compounding of rewards")
    # user_id will be derived from the authenticated user context

class UnstakeRequest(BaseModel):
    """
    Schema used when a user initiates an unstaking action.
    """
    staking_position_id: uuid.UUID = Field(..., description="The ID of the staking position to unstake from")
    # Optional: Specify amount to partially unstake if supported
    amount: Optional[Decimal] = Field(None, gt=0, description="Amount to unstake (if partial unstake is allowed, otherwise unstakes all)")
    # user_id will be derived from the authenticated user context


# --- Staking Position and History Schemas ---

class InterestAccrualBase(BaseModel):
    """ Base schema for interest accrual records. """
    amount: Decimal
    apy_at_accrual: Decimal
    accrual_date: datetime

    class ConfigDict:
        from_attributes = True

class InterestAccrual(InterestAccrualBase):
    """ Full schema for an interest accrual record. """
    id: uuid.UUID
    staking_position_id: uuid.UUID


class StakingPositionBase(BaseModel):
    """ Base schema for staking position details. """
    token_symbol: str
    chain: Chain
    amount: Decimal
    apy_at_stake: Decimal
    is_compounding: bool
    start_date: datetime
    protocol_address: Optional[str] = None

    class ConfigDict:
        from_attributes = True


class StakingPosition(StakingPositionBase):
    """
    Schema representing a complete staking position object returned by the API.
    Includes database-generated ID and user ID.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Optionally include recent accruals or total interest earned
    total_interest_earned: Optional[Decimal] = Field(None, description="Calculated total interest earned on this position")


class StakingHistoryResponse(BaseModel):
    """ Schema for returning a list of interest accruals for a position. """
    staking_position_id: uuid.UUID
    accruals: List[InterestAccrual]
    page: int
    limit: int
    total: int
