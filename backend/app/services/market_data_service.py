import json
import logging
import httpx
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.utils.exceptions import ServiceUnavailableException
from app.schemas.market import MarketCoin, ChartDataPoint, ChartDataResponse

# Configure logger
logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Service for fetching and caching cryptocurrency market data.
    Primary Source: CoinGecko API
    Cache Layer: Redis (simulated via internal dict if Redis not available, 
    but designed for Redis).
    """

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.pro_url = "https://pro-api.coingecko.com/api/v3"
        
        # Use Pro API if key is provided, otherwise free API
        if settings.COINGECKO_API_KEY:
            self.api_url = self.pro_url
            self.headers = {"x-cg-pro-api-key": settings.COINGECKO_API_KEY}
        else:
            self.api_url = self.base_url
            self.headers = {}

        # Cache TTLs
        self.PRICE_CACHE_TTL = 60  # 1 minute for current prices
        self.CHART_CACHE_TTL = 300 # 5 minutes for charts
        self.LIST_CACHE_TTL = 3600 # 1 hour for coin lists

        # Map internal symbols to CoinGecko IDs
        # In production, this should be in the Token database table.
        self.symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "usdc": "usd-coin",
            "usdt": "tether",
            "matic": "matic-network",
            "bnb": "binancecoin",
            "base": "base", # Note: Base is a chain, not a token, but might look up ETH on Base
        }

    async def get_current_price(self, coin_id: str, currency: str = "usd") -> Decimal:
        """
        Get the current price of a single coin.
        """
        data = await self.get_current_prices([coin_id], currency)
        return data.get(coin_id, Decimal(0))

    async def get_current_prices(self, coin_ids: List[str], currency: str = "usd") -> Dict[str, Decimal]:
        """
        Get current prices for multiple coins.
        """
        # 1. Check Cache (Pseudocode - assumes a redis_client is available globally or passed in)
        # For this implementation, we will skip direct Redis code to keep it self-contained,
        # but in production: 
        # cached = redis.mget(coin_ids) ...
        
        # 2. Fetch from API
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": currency
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/simple/price", 
                    params=params, 
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                result = {}
                for cid in coin_ids:
                    if cid in data and currency in data[cid]:
                        result[cid] = Decimal(str(data[cid][currency]))
                    else:
                        result[cid] = Decimal(0)
                
                return result
                
        except httpx.RequestError as e:
            logger.error(f"CoinGecko Request Error: {e}")
            raise ServiceUnavailableException("Market Data Provider")

    async def get_market_list(
        self, currency: str = "usd", limit: int = 100, page: int = 1
    ) -> List[MarketCoin]:
        """
        Get a ranked list of coins with market data (Market Cap, Volume, Change).
        """
        params = {
            "vs_currency": currency,
            "order": "market_cap_desc",
            "per_page": limit,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/coins/markets", 
                    params=params, 
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                market_coins = []
                for item in data:
                    market_coins.append(MarketCoin(
                        id=item['id'],
                        symbol=item['symbol'],
                        name=item['name'],
                        image=item.get('image'),
                        current_price=Decimal(str(item.get('current_price', 0))),
                        market_cap=Decimal(str(item.get('market_cap', 0))),
                        market_cap_rank=item.get('market_cap_rank'),
                        total_volume=Decimal(str(item.get('total_volume', 0))),
                        price_change_percentage_24h=item.get('price_change_percentage_24h')
                    ))
                
                return market_coins

        except httpx.RequestError as e:
            logger.error(f"CoinGecko Market List Error: {e}")
            raise ServiceUnavailableException("Market Data Provider")

    async def get_coin_chart(
        self, coin_id: str, currency: str = "usd", days: str = "1"
    ) -> ChartDataResponse:
        """
        Get historical chart data (price vs time).
        days: '1', '7', '30', '365', 'max'
        """
        params = {
            "vs_currency": currency,
            "days": days
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/coins/{coin_id}/market_chart", 
                    params=params, 
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                prices = data.get("prices", [])
                
                points = []
                for p in prices:
                    # p is [timestamp, price]
                    points.append(ChartDataPoint(
                        timestamp=int(p[0]),
                        price=Decimal(str(p[1]))
                    ))
                
                return ChartDataResponse(
                    coin_id=coin_id,
                    currency=currency,
                    timeframe=f"{days}D",
                    data_points=points
                )

        except httpx.RequestError as e:
            logger.error(f"CoinGecko Chart Error: {e}")
            raise ServiceUnavailableException("Market Data Provider")

    def get_id_from_symbol(self, symbol: str) -> Optional[str]:
        """
        Helper to resolve symbol to ID using internal map.
        """
        return self.symbol_map.get(symbol.lower())