from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate, 
    InvoiceUpdate, 
    Invoice, 
    InvoicePublicView
)
from app.services.invoice_service import InvoiceService
from app.utils.exceptions import NotFoundException, BadRequestException, NotAuthorizedException

router = APIRouter()

@router.post("/", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new invoice.
    Returns the invoice object containing the unique `payment_link_id`.
    """
    invoice_service = InvoiceService(db)
    return await invoice_service.create_invoice(current_user.id, invoice_in)

@router.get("/", response_model=List[Invoice])
async def get_my_invoices(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List invoices created by the current user.
    """
    invoice_service = InvoiceService(db)
    return await invoice_service.get_user_invoices(current_user.id, skip, limit)

@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice_detail(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get details of a specific invoice (Internal View).
    """
    invoice_service = InvoiceService(db)
    try:
        return await invoice_service.get_invoice_details(invoice_id, current_user.id)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    except NotAuthorizedException:
        raise HTTPException(status_code=403, detail="Not authorized to view this invoice.")

@router.post("/{invoice_id}/cancel", response_model=Invoice)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Cancel a pending invoice.
    """
    invoice_service = InvoiceService(db)
    try:
        return await invoice_service.cancel_invoice(invoice_id, current_user.id)
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=e.detail)

@router.get("/public/{payment_link_id}", response_model=InvoicePublicView)
async def get_public_invoice_view(
    payment_link_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Public endpoint to fetch invoice details for the payer.
    No authentication required.
    """
    invoice_service = InvoiceService(db)
    try:
        return await invoice_service.get_public_invoice(payment_link_id)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Invoice not found.")