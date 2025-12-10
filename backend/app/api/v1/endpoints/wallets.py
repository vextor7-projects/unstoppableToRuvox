from typing import Any, List
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.wallet import TokenBalance, Wallet
from app.schemas.wallet import (
    PortfolioCreate, 
    Portfolio as PortfolioSchema, 
    WalletAddRequest,
    Wallet as WalletSchema,
    BalanceResponse,
    TokenBalanceBase
)
from app.services.wallet_service import WalletService
from app.utils.exceptions import BadRequestException, NotFoundException, ConflictException

router = APIRouter()

# --- Portfolio Management ---

@router.post("/portfolios", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    wallet_service = WalletService(db)
    portfolio = await wallet_service.create_portfolio(current_user.id, portfolio_in.name)
    await db.commit() # Commit transaction
    return portfolio

@router.get("/portfolios", response_model=List[PortfolioSchema])
async def read_portfolios(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    wallet_service = WalletService(db)
    return await wallet_service.get_user_portfolios(current_user.id)

# --- Wallet Management ---

@router.post("/add", response_model=WalletSchema, status_code=status.HTTP_201_CREATED)
async def add_wallet(
    wallet_in: WalletAddRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a wallet address to a portfolio.
    Keys are generated client-side. Server stores public address only.
    """
    wallet_service = WalletService(db)
    try:
        wallet = await wallet_service.register_wallet(current_user.id, wallet_in)
        await db.commit() # Commit transaction
        return wallet
    except (NotFoundException, ConflictException) as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=e.detail)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(e))

# --- Balances ---

@router.post("/portfolios/{portfolio_id}/sync")
async def sync_portfolio(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Trigger a background sync of balances.
    """
    wallet_service = WalletService(db)
    # Check ownership
    await wallet_service.get_portfolio(portfolio_id, current_user.id)
    
    # Run sync (blocks for now, ideally background task)
    await wallet_service.sync_portfolio_balances(portfolio_id)
    await db.commit()
    
    return {"message": "Sync complete."}

@router.get("/portfolios/{portfolio_id}/balances", response_model=BalanceResponse)
async def get_portfolio_balances(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get aggregated balances for a portfolio.
    """
    wallet_service = WalletService(db)
    # Check ownership
    await wallet_service.get_portfolio(portfolio_id, current_user.id)
    
    # Aggregate balances via SQL
    stmt = select(TokenBalance).join(Wallet).where(Wallet.portfolio_id == portfolio_id)
    result = await db.execute(stmt)
    balances = result.scalars().all()
    
    total_usd = sum(b.usd_value for b in balances)
    
    return BalanceResponse(
        total_usd_value=total_usd,
        balances=[TokenBalanceBase.model_validate(b) for b in balances]
    )