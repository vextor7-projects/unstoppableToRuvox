from typing import Any, List, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_superuser
from app.services.admin_service import AdminService
from app.schemas.user import User as UserSchema
from app.utils.enums import UserStatus, SuspiciousActivityStatus
from app.utils.exceptions import NotFoundException, BadRequestException

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    current_user: UserSchema = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get overview metrics for the Admin Dashboard.
    """
    service = AdminService(db)
    return await service.get_dashboard_stats()

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AdminService(db)
    return await service.get_all_users(skip, limit)

@router.patch("/users/{user_id}/status", response_model=UserSchema)
async def update_user_status(
    user_id: uuid.UUID,
    status: UserStatus = Body(..., embed=True),
    current_user: UserSchema = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Freeze or Activate a user account.
    """
    service = AdminService(db)
    try:
        return await service.update_user_status(user_id, status)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found.")
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=e.detail)

@router.get("/compliance/suspicious", response_model=List[Dict[str, Any]])
async def list_suspicious_activities(
    status_filter: SuspiciousActivityStatus = None,
    current_user: UserSchema = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AdminService(db)
    return await service.get_suspicious_activities(status_filter)

@router.post("/compliance/suspicious/{activity_id}/resolve")
async def resolve_activity(
    activity_id: uuid.UUID,
    resolution: SuspiciousActivityStatus = Body(..., embed=True),
    notes: str = Body(..., embed=True),
    current_user: UserSchema = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Resolve a compliance flag (e.g., mark as False Positive or Confirmed Fraud).
    """
    service = AdminService(db)
    try:
        await service.resolve_suspicious_activity(
            activity_id, resolution, notes, current_user.username
        )
        return {"message": "Activity resolved successfully."}
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Activity not found.")