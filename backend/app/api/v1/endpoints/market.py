from typing import Any, List, Dict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.schemas.market import (
    MarketCoin, 
    ChartDataResponse,
    PriceAlert, 
    PriceAlertCreate, 
    PriceAlertUpdate
)
from app.services.market_data_service import MarketDataService
from app.crud.crud_market import crud_price_alert
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.exceptions import ServiceUnavailableException, NotFoundException

router = APIRouter()

@router.get("/list", response_model=List[MarketCoin])
async def get_market_list(
    currency: str = "usd",
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get top coins by market cap.
    """
    service = MarketDataService()
    try:
        return await service.get_market_list(currency=currency, page=page, limit=limit)
    except ServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=e.detail)

@router.get("/price/{coin_id}", response_model=Dict[str, Decimal])
async def get_price(
    coin_id: str,
    currency: str = "usd",
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current price for a specific coin.
    """
    service = MarketDataService()
    try:
        price = await service.get_current_price(coin_id, currency)
        return {"price": price}
    except ServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=e.detail)

@router.get("/chart/{coin_id}", response_model=ChartDataResponse)
async def get_chart(
    coin_id: str,
    days: str = Query("1", pattern="^(1|7|14|30|90|180|365|max)$"),
    currency: str = "usd",
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get historical chart data.
    Days can be: 1, 7, 14, 30, 90, 180, 365, max.
    """
    service = MarketDataService()
    try:
        return await service.get_coin_chart(coin_id, currency, days)
    except ServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=e.detail)

# --- Price Alerts ---

@router.post("/alerts", response_model=PriceAlert, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_in: PriceAlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new price alert for the user.
    """
    return await crud_price_alert.create_with_user(
        db, obj_in=alert_in, user_id=current_user.id
    )

@router.get("/alerts", response_model=List[PriceAlert])
async def get_my_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all active price alerts for the user.
    """
    return await crud_price_alert.get_by_user(db, user_id=current_user.id)

@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_price_alert(
    alert_id: str, # UUID string
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a price alert.
    """
    import uuid
    try:
        u_id = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify ownership logic would go here or in CRUD.
    # Ideally crud_price_alert.get(db, id=u_id) then check user_id
    
    alert = await crud_price_alert.get(db, id=u_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await crud_price_alert.remove(db, id=u_id)
    return None