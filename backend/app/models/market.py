import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Numeric,
    Text,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import PriceAlertDirection, PriceAlertStatus


class PriceAlert(Base):
    """
    Stores a user-defined price alert for a specific coin.
    (Stage 14)
    """
    __tablename__ = "price_alert"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user_account.id"), 
        nullable=False, 
        index=True
    )
    
    # Coin identifier (e.g., "solana", "bitcoin" from CoinGecko)
    coin_id = Column(String(100), nullable=False, index=True)
    
    target_price = Column(Numeric(36, 18), nullable=False)
    
    # The currency of the target price (e.g., "USD")
    currency = Column(String(10), default="USD", nullable=False)
    
    direction = Column(
        Enum(PriceAlertDirection), 
        default=PriceAlertDirection.ABOVE, 
        nullable=False
    )
    
    status = Column(
        Enum(PriceAlertStatus), 
        default=PriceAlertStatus.ACTIVE, 
        nullable=False, 
        index=True
    )
    
    triggered_at = Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    
    user = relationship("User", back_populates="price_alerts")


class PriceSnapshot(Base):
    """
    Stores historical price data snapshots for auditing or chart generation.
    (Stage 14)
    """
    __tablename__ = "price_snapshot"

    # Coin identifier (e.g., "solana")
    coin_id = Column(String(100), primary_key=True, index=True)
    
    # Currency of the price (e.g., "USD")
    currency = Column(String(10), primary_key=True, default="USD")
    
    price = Column(Numeric(36, 18), nullable=False)
    
    market_cap = Column(Numeric(36, 4), nullable=True)
    total_volume_24h = Column(Numeric(36, 4), nullable=True)
    
    snapshot_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        primary_key=True
    )
