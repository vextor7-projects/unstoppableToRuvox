import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, AnyHttpUrl

from app.utils.enums import PriceAlertDirection, PriceAlertStatus

# --- Price Alert Schemas ---

class PriceAlertBase(BaseModel):
    """
    Base schema for price alert information.
    """
    coin_id: str = Field(..., description="Coin identifier (e.g., 'solana', 'bitcoin' from CoinGecko)")
    target_price: Decimal = Field(..., gt=0, description="The target price for the alert")
    currency: str = Field("USD", max_length=10, description="The currency of the target price (e.g., 'USD')")
    direction: PriceAlertDirection = Field(PriceAlertDirection.ABOVE, description="Trigger when price is ABOVE or BELOW the target")

    class ConfigDict:
        from_attributes = True # Allow creating schema from ORM model

class PriceAlertCreate(PriceAlertBase):
    """
    Schema used when a user creates a new price alert.
    user_id will be derived from the authenticated user context.
    """
    pass # Inherits fields from PriceAlertBase

class PriceAlertUpdate(BaseModel):
    """
    Schema for updating an existing price alert.
    Allows changing target price, direction, or activating/deactivating.
    """
    target_price: Optional[Decimal] = Field(None, gt=0)
    direction: Optional[PriceAlertDirection] = None
    status: Optional[PriceAlertStatus] = Field(None, description="Set to ACTIVE or INACTIVE")

class PriceAlert(PriceAlertBase):
    """
    Schema representing a complete price alert object returned by the API.
    Includes database-generated fields.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    status: PriceAlertStatus
    triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# --- Market Data Schemas ---

class MarketCoin(BaseModel):
    """
    Schema representing basic information about a coin in market lists.
    """
    id: str = Field(..., description="CoinGecko ID (e.g., 'solana')")
    symbol: str = Field(..., description="Token symbol (e.g., 'SOL')")
    name: str = Field(..., description="Coin name (e.g., 'Solana')")
    image: Optional[AnyHttpUrl] = Field(None, description="URL to the coin's image")
    current_price: Optional[Decimal] = Field(None, description="Current price in the requested currency")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    market_cap_rank: Optional[int] = Field(None, description="Market cap rank")
    total_volume: Optional[Decimal] = Field(None, description="Total trading volume in the last 24h")
    price_change_percentage_24h: Optional[float] = Field(None, description="Price change percentage in the last 24h")
    # Add other fields as needed from CoinGecko/CoinMarketCap

class ChartDataPoint(BaseModel):
    """
    Represents a single data point for a price chart (timestamp, value).
    """
    timestamp: int = Field(..., description="Unix timestamp (in milliseconds or seconds, consistent with API)")
    price: Decimal = Field(..., description="Price at the given timestamp")

class ChartDataResponse(BaseModel):
    """
    Schema for returning chart data for a specific coin and timeframe.
    """
    coin_id: str
    currency: str
    timeframe: str # e.g., "1D", "1W", "1M"
    data_points: List[ChartDataPoint]

# --- Price Snapshot Schemas (Primarily for internal logging/auditing) ---

class PriceSnapshotBase(BaseModel):
    """ Base schema for price snapshot data. """
    coin_id: str
    currency: str
    price: Decimal
    market_cap: Optional[Decimal] = None
    total_volume_24h: Optional[Decimal] = None

    class ConfigDict:
        from_attributes = True

class PriceSnapshot(PriceSnapshotBase):
    """ Schema representing a price snapshot record. """
    snapshot_at: datetime
