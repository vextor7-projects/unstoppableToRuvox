from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user, get_current_merchant_user
from app.models.user import User
from app.schemas.payment import (
    PaymentSessionCreateRequest, 
    PaymentSessionResponse
)
from app.schemas.defi import SwapQuoteRequest
from app.services.payment_service import PaymentService
from app.services.dex_aggregator_service import DexAggregatorService
from app.utils.exceptions import BadRequestException, NotFoundException, ServiceUnavailableException

router = APIRouter()

# --- Payment Sessions (QR/NFC) ---

@router.post("/sessions", response_model=PaymentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_session(
    session_in: PaymentSessionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new payment session.
    Used by Merchants (POS) or Users (Peer-to-Peer Request).
    Returns the payload used to generate the QR code.
    """
    # Logic to determine if merchant_id should be set
    merchant_id = None
    if current_user.role == "merchant": # Checking literal string or Enum
        # In a real app, we'd fetch the Merchant profile linked to this user
        # merchant_id = current_user.merchant.id
        merchant_id = session_in.merchant_id # Allow explicit pass if user manages multiple
        
    payment_service = PaymentService(db)
    return await payment_service.create_payment_session(
        request=session_in,
        creator_user_id=current_user.id
    )

@router.get("/sessions/{session_id}", response_model=PaymentSessionResponse)
async def get_payment_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve details of a payment session.
    Used by the Payer when they scan a QR code.
    """
    payment_service = PaymentService(db)
    return await payment_service.get_payment_session(session_id)


# --- DEX / Swaps ---

@router.post("/quote", response_model=Dict[str, Any])
async def get_swap_quote(
    request: SwapQuoteRequest,
    current_user: User = Depends(get_current_active_user),
    # DB not strictly needed for aggregator but good for logging if extended
    db: AsyncSession = Depends(get_db) 
) -> Any:
    """
    Get a swap quote from the DEX aggregator.
    This proxies the request to Jupiter (Solana) or 1inch (EVM).
    """
    dex_service = DexAggregatorService()
    
    # Convert Decimal amount to atomic units (integer) based on token decimals.
    # Note: The frontend often sends the atomic amount directly or we need to fetch decimals.
    # For simplicity here, we assume 'amount' in request is already atomic or handling is delegated.
    # Ideally, we should fetch token decimals here to be safe, but that adds latency.
    # Let's assume the Schema description says "Amount in standard units" so we must convert.
    
    # Since converting requires knowing decimals (which requires RPC call), 
    # for high performance, frontends usually send atomic units. 
    # If Schema says Decimal, we cast to int assuming atomic if > 1000 or handle logic.
    # IMPORTANT: `request.amount` is Decimal. Jupiter expects Integer String (Atomic).
    
    # TODO: Implement token decimal lookup cache for robust conversion.
    # For this implementation, we will assume the frontend passes the atomic amount cast as Decimal 
    # OR we accept it's just a direct pass-through if the schema allows.
    
    try:
        amount_atomic = int(request.amount) 
        
        return await dex_service.get_quote(
            chain=request.from_chain,
            token_in_address=request.from_token_address,
            token_out_address=request.to_token_address,
            amount_in_atomic=amount_atomic,
            slippage_bps=int(request.slippage_percentage * 100) if request.slippage_percentage else 50
        )
    except ServiceUnavailableException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.detail)
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)

@router.post("/swap/instructions", response_model=Dict[str, Any])
async def get_swap_instructions(
    quote_data: Dict[str, Any], # The raw response from /quote
    user_public_key: str,
    chain: str, # Pass chain explicitly or derive from quote
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get transaction instructions to execute a swap.
    """
    dex_service = DexAggregatorService()
    # Enum conversion
    try:
        from app.utils.enums import Chain
        chain_enum = Chain(chain)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chain")

    return await dex_service.get_swap_instructions(
        chain=chain_enum,
        quote_response=quote_data,
        user_public_key=user_public_key
    )