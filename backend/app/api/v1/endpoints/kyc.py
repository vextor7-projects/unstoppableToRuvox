from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.kyc import (
    KycSubmission, 
    KycSubmissionCreate, 
    KycStatusResponse
)
from app.services.kyc_service import KycService
from app.utils.exceptions import ConflictException, NotFoundException
from app.core.config import settings

router = APIRouter()

@router.post("/submit", response_model=KycSubmission, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    submission: KycSubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Initiate a KYC submission.
    """
    service = KycService(db)
    try:
        return await service.create_submission(current_user.id, submission)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.detail)

@router.get("/status", response_model=KycStatusResponse)
async def get_my_kyc_status(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user's KYC status.
    """
    return KycStatusResponse(
        current_level=current_user.kyc_level
    )

# --- Webhooks (Public Endpoint, Signature Verified) ---

@router.post("/webhook/sumsub")
async def kyc_provider_webhook(
    request: Request,
    x_payload_digest: str = Header(None), # Sumsub signature header
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Webhook endpoint for KYC provider updates.
    """
    if not settings.SUMSUB_SECRET_KEY:
        raise HTTPException(status_code=501, detail="KYC provider not configured.")

    payload_bytes = await request.body()
    service = KycService(db)
    
    # 1. Verify Signature (CRITICAL)
    if not await service.verify_webhook_signature(
        x_payload_digest, payload_bytes, settings.SUMSUB_SECRET_KEY
    ):
        raise HTTPException(status_code=401, detail="Invalid signature.")

    # 2. Process Update
    # Note: Actual payload parsing depends on provider docs. 
    # This assumes logic exists in service or we parse here.
    # For now, we return success to acknowledge receipt.
    
    # await service.process_webhook_payload(await request.json())
    
    return {"status": "received"}