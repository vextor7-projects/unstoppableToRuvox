import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from app.utils.enums import InvoiceStatus

# --- Base Invoice Schema ---

class InvoiceBase(BaseModel):
    """
    Base schema containing common fields for an invoice.
    """
    amount_fiat: Decimal = Field(..., gt=0, description="Amount due in fiat currency")
    fiat_currency: str = Field("USD", max_length=10, description="Fiat currency code (e.g., USD, KRW)")
    payer_email: Optional[EmailStr] = Field(None, description="Email of the person being billed")
    description: Optional[str] = Field(None, description="Description of the invoice item/service")
    due_date: Optional[date] = Field(None, description="Date the invoice payment is due")

    class Config:
        from_attributes = True


# --- Schema for Creating an Invoice ---

class InvoiceCreate(InvoiceBase):
    """
    Schema used when creating a new invoice via the API.
    creator_user_id will be derived from the authenticated user context.
    """
    pass # Inherits all fields from InvoiceBase


# --- Schema for Updating an Invoice ---
# Typically, only status or perhaps description might be updatable after creation.
# Payment details are usually immutable once paid.

class InvoiceUpdate(BaseModel):
    """
    Schema for updating an existing invoice (limited fields).
    """
    status: Optional[InvoiceStatus] = None # e.g., Mark as cancelled
    description: Optional[str] = None
    due_date: Optional[date] = None


# --- Schema for Reading/Returning an Invoice ---

class Invoice(InvoiceBase):
    """
    Schema representing a complete invoice object returned by the API.
    Includes database-generated fields.
    """
    id: uuid.UUID
    creator_user_id: uuid.UUID
    status: InvoiceStatus
    payment_link_id: str # The unique ID for the shareable link
    paid_at: Optional[datetime] = None
    payment_transaction_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


# --- Schema for Public Invoice View (via payment link) ---

class InvoicePublicView(BaseModel):
    """
    Schema for the data shown when someone accesses the public payment link.
    Excludes sensitive creator information.
    """
    invoice_id: uuid.UUID
    payment_link_id: str
    amount_fiat: Decimal
    fiat_currency: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: InvoiceStatus # To show if already paid/cancelled
    creator_display_name: Optional[str] = Field(None, description="Creator's username or business name")

    class Config:
        from_attributes = True # Allow mapping from Invoice model
