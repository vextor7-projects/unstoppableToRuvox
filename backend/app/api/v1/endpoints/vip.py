from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.vip import VipStatusResponse
from app.crud.crud_vip import crud_vip_tier

router = APIRouter()

@router.get("/status", response_model=VipStatusResponse)
async def get_vip_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get current user's VIP status and progress.
    """
    vip_tier = await crud_vip_tier.get_by_user(db, user_id=current_user.id)
    if not vip_tier:
        # Should have been created, but if missing return default
        # In real app, trigger creation here or return default object
        from app.utils.enums import VipTierLevel
        return {
            "tier": VipTierLevel.BRONZE, 
            "monthly_transaction_volume": 0, 
            "current_staking_value": 0,
            "volume_reset_date": "2025-01-01T00:00:00Z", # Placeholder
            "user_id": current_user.id
        }
        
    return vip_tier