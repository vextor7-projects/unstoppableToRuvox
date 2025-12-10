from typing import Any, List
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.exchange import (
    InternalTransferRequest,
    InternalTransferResponse,
    DepositAddressResponse,
    InternalBalanceResponse,
    WithdrawalRequestCreate,
    WithdrawalRequest as WithdrawalRequestSchema,
    DepositTransaction as DepositTransactionSchema
)
from app.services.exchange_service import ExchangeService
from app.utils.enums import Chain
from app.utils.exceptions import (
    BadRequestException,
    NotFoundException,
    InsufficientBalanceException,
    InternalLedgerException,
    InvalidTotpCodeException,
    ConflictException
)

router = APIRouter()

# --- Internal Transfers ---

@router.post("/transfer", response_model=InternalTransferResponse)
async def internal_transfer(
    request: InternalTransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Execute an instant off-chain transfer to another user.
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive.")

    exchange_service = ExchangeService(db)
    try:
        # Atomic transaction handled within service (flush) -> commit here if needed
        # But ExchangeService.internal_transfer usually handles commit.
        # Let's verify service implementation: Yes, it commits.
        return await exchange_service.internal_transfer(current_user.id, request)
    except (NotFoundException, InsufficientBalanceException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except InternalLedgerException as e:
        raise HTTPException(status_code=500, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Transfer failed.")


# --- Deposits ---

@router.get("/deposit/address/{chain}", response_model=DepositAddressResponse)
async def get_deposit_address(
    chain: Chain,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the deposit address for a specific chain.
    """
    exchange_service = ExchangeService(db)
    try:
        return await exchange_service.get_deposit_address(current_user.id, chain)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.get("/deposit/history", response_model=List[DepositTransactionSchema])
async def get_deposit_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    exchange_service = ExchangeService(db)
    return await exchange_service.get_deposit_history(current_user.id, limit)


# --- Withdrawals ---

@router.post("/withdrawal/request", response_model=WithdrawalRequestSchema, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    request: WithdrawalRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request a withdrawal to an external blockchain address.
    **CRITICAL:** Requires 2FA code if enabled on account.
    """
    exchange_service = ExchangeService(db)
    try:
        return await exchange_service.request_withdrawal(current_user.id, request)
    except InvalidTotpCodeException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid or missing 2FA code."
        )
    except InsufficientBalanceException as e:
        raise HTTPException(status_code=400, detail=e.detail)
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=e.detail)


@router.get("/withdrawal/history", response_model=List[WithdrawalRequestSchema])
async def get_withdrawal_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    exchange_service = ExchangeService(db)
    return await exchange_service.get_withdrawal_history(current_user.id, limit)


# --- Balances ---

@router.get("/balance/{token_symbol}", response_model=InternalBalanceResponse)
async def get_internal_balance(
    token_symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    exchange_service = ExchangeService(db)
    return await exchange_service.get_internal_balance(current_user.id, token_symbol)