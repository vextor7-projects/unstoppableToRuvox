from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.staking import (
    StakeRequest, 
    StakingPosition, 
    StakingOption
)
from app.services.staking_service import StakingService
from app.utils.exceptions import BadRequestException, NotFoundException

router = APIRouter()

@router.get("/options", response_model=List[StakingOption])
async def get_staking_options(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get available staking pools.
    """
    service = StakingService(db)
    return await service.get_staking_options()

@router.post("/", response_model=StakingPosition, status_code=status.HTTP_201_CREATED)
async def stake_funds(
    stake_in: StakeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Stake funds from internal balance.
    """
    service = StakingService(db)
    try:
        return await service.stake_funds(current_user.id, stake_in)
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=e.detail)

@router.get("/", response_model=List[StakingPosition])
async def get_my_positions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get active staking positions.
    """
    service = StakingService(db)
    return await service.get_user_positions(current_user.id)

@router.post("/{position_id}/unstake", response_model=StakingPosition)
async def unstake_funds(
    position_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Unstake funds and claim interest.
    """
    service = StakingService(db)
    try:
        return await service.unstake_funds(current_user.id, position_id)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Position not found.")