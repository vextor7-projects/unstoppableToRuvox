import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr

from app.utils.enums import (
    Chain,
    KycStatus,
    SettlementStatus,
    SettlementFrequency,
    MerchantEmployeeRole
)

# --- Merchant Schemas ---

class MerchantBase(BaseModel):
    """
    Base schema for merchant profile information.
    """
    business_name: str = Field(..., max_length=255, description="Registered business name")
    business_type: Optional[str] = Field(None, max_length=100, description="Type of business (e.g., Retail, Service)")
    registration_number: Optional[str] = Field(None, max_length=100, description="Business registration number")
    business_address: Optional[str] = Field(None, description="Physical address of the business")
    
    # Settlement preferences
    settlement_frequency: SettlementFrequency = SettlementFrequency.DAILY
    settlement_wallet_address: Optional[str] = Field(None, description="Wallet address for receiving settlements")
    settlement_chain: Optional[Chain] = Field(None, description="Blockchain for settlements")
    settlement_token_symbol: Optional[str] = Field("USDC", max_length=20, description="Token for settlements")

    class Config:
        from_attributes = True

class MerchantCreate(MerchantBase):
    """
    Schema used when a user registers as a merchant.
    user_id will be derived from the authenticated user.
    """
    pass # Inherits fields from MerchantBase

class MerchantUpdate(MerchantBase):
    """
    Schema for updating merchant profile information.
    Allows updating non-critical fields.
    """
    business_name: Optional[str] = Field(None, max_length=255)
    settlement_frequency: Optional[SettlementFrequency] = None
    settlement_wallet_address: Optional[str] = None
    settlement_chain: Optional[Chain] = None
    settlement_token_symbol: Optional[str] = Field(None, max_length=20)


class Merchant(MerchantBase):
    """
    Schema representing a complete merchant object returned by the API.
    Includes user_id and KYC status.
    """
    user_id: uuid.UUID # Corresponds to the linked user account ID
    kyc_status: KycStatus
    created_at: datetime
    updated_at: datetime


# --- Merchant KYC Schemas ---

class MerchantKycBase(BaseModel):
    """
    Base schema for merchant KYC submission data.
    """
    document_type: str = Field(..., max_length=100, description="Type of document (e.g., BUSINESS_REGISTRATION)")
    # Actual file upload handled separately, this schema might receive S3 keys
    document_s3_key: str = Field(..., description="S3 key for the main document")
    address_proof_s3_key: Optional[str] = Field(None, description="S3 key for address proof document, if required")

    class Config:
        from_attributes = True

class MerchantKycSubmit(MerchantKycBase):
    """
    Schema for submitting merchant KYC documents.
    """
    pass # Inherits fields

class MerchantKycReview(BaseModel):
    """
    Schema used by admins to review/update merchant KYC status.
    """
    status: KycStatus
    review_notes: Optional[str] = None

class MerchantKyc(MerchantKycBase):
    """
    Schema representing a merchant KYC submission record returned by the API.
    """
    merchant_user_id: uuid.UUID
    status: KycStatus
    review_notes: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


# --- Merchant Settlement Schemas ---

class SettlementDetailBase(BaseModel):
    """ Base schema for a settlement detail record (links payment to settlement). """
    payment_transaction_id: uuid.UUID

    class Config:
        from_attributes = True

class SettlementDetail(SettlementDetailBase):
    settlement_id: uuid.UUID
    # Potentially include basic payment details here if needed
    

class MerchantSettlementBase(BaseModel):
    """
    Base schema for merchant settlement information.
    """
    period_start: datetime
    period_end: datetime
    total_volume_fiat: Decimal
    total_fee_fiat: Decimal
    settlement_amount_fiat: Decimal
    settlement_token_symbol: str
    settlement_token_amount: Decimal
    settlement_wallet_address: str
    settlement_chain: Chain

    class Config:
        from_attributes = True

class MerchantSettlementCreate(MerchantSettlementBase):
    """ Schema for creating a settlement record (likely internal use). """
    merchant_id: uuid.UUID

class MerchantSettlement(MerchantSettlementBase):
    """
    Schema representing a complete settlement record returned by the API.
    """
    id: uuid.UUID
    merchant_id: uuid.UUID
    status: SettlementStatus
    requested_at: datetime
    processed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None # Blockchain tx hash for the payout
    
    # Optional: Include details if needed for display
    details: List[SettlementDetail] = []


# --- Merchant Employee Schemas ---

class MerchantEmployeeBase(BaseModel):
    """ Base schema for merchant employee information. """
    email: EmailStr
    role: MerchantEmployeeRole = MerchantEmployeeRole.CASHIER

    class Config:
        from_attributes = True

class MerchantEmployeeCreate(MerchantEmployeeBase):
    """ Schema for creating a new merchant employee. Requires password. """
    password: str = Field(..., min_length=8) # Or integrate with invite system

class MerchantEmployeeUpdate(BaseModel):
    """ Schema for updating a merchant employee (e.g., role, status). """
    role: Optional[MerchantEmployeeRole] = None
    is_active: Optional[bool] = None

class MerchantEmployee(MerchantEmployeeBase):
    """ Schema representing a merchant employee returned by the API (excludes password). """
    id: uuid.UUID
    merchant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Merchant Terminal Schemas ---

class MerchantTerminalBase(BaseModel):
    """ Base schema for merchant terminal information. """
    terminal_name: str = Field(..., max_length=100)

    class Config:
        from_attributes = True

class MerchantTerminalCreate(MerchantTerminalBase):
    """ Schema for creating a new merchant terminal (API key generated server-side). """
    pass

class MerchantTerminalUpdate(BaseModel):
    """ Schema for updating a merchant terminal (e.g., name, status). """
    terminal_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class MerchantTerminalApiKeyResponse(BaseModel):
    """ Schema for returning a newly generated API key (only shown once). """
    terminal_id: uuid.UUID
    terminal_name: str
    api_key: str # The plain-text key

class MerchantTerminal(MerchantTerminalBase):
    """ Schema representing a merchant terminal returned by the API (excludes API key). """
    id: uuid.UUID
    merchant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
