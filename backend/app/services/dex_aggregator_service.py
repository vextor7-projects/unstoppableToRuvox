import httpx
import logging
from typing import Dict, Any
from app.core.config import settings
from app.utils.enums import Chain
from app.utils.constants import SLIPPAGE_TOLERANCE_DEFAULT
from app.utils.exceptions import ServiceUnavailableException, BadRequestException, AppException
from decimal import Decimal

logger = logging.getLogger(__name__)

class DexAggregatorService:
    def __init__(self):
        self.jupiter_api_url = "https://quote-api.jup.ag/v6"
        self.oneinch_api_url = "https://api.1inch.dev/swap/v5.2"
        self.oneinch_headers = {
            "Authorization": f"Bearer {settings.ONEINCH_API_KEY}"
        } if settings.ONEINCH_API_KEY else {}

    
    async def get_token_price(self, token_symbol: str, vs_token: str = "USDC") -> Decimal:
        """
        Get current price of a token in USDC/USDT.
        Used for reverse quote estimation.
        """
        # Mapping symbol to Jupiter Mint IDs (simplified)
        mints = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        }
        mint_id = mints.get(token_symbol.upper())
        if not mint_id:
            # Fallback to 1.0 for stables or throw
            if token_symbol.upper() in ["USDC", "USDT"]: return Decimal(1)
            # Note: For production, you might want to call an external API like CoinGecko here
            # instead of raising immediately if it's not in the hardcoded map.
            logger.warning(f"Price feed mint not found for {token_symbol}, defaulting to 0")
            return Decimal(0)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.jupiter_price_url}?ids={mint_id}")
                data = resp.json()
                price = data.get("data", {}).get(mint_id, {}).get("price")
                return Decimal(str(price)) if price else Decimal(0)
            except Exception as e:
                logger.error(f"Price fetch error: {e}")
                raise ServiceUnavailableException("Price API")


    async def get_quote(
        self,
        chain: Chain,
        token_in_address: str,
        token_out_address: str,
        amount_atomic: int,
        slippage_bps: int = int(SLIPPAGE_TOLERANCE_DEFAULT * 10000),
        swap_mode: str = "ExactIn"  # "ExactIn" or "ExactOut"
    ) -> Dict[str, Any]:
        try:
            if chain == Chain.SOLANA:
                return await self._get_jupiter_quote(
                    token_in_address, token_out_address, amount_atomic, slippage_bps, swap_mode
                )
            elif chain in [Chain.ETHEREUM, Chain.POLYGON, Chain.BASE]:
                # 1inch typically defaults to ExactIn; ExactOut support varies by endpoint/version.
                # For high reliability in this implementation, we throw if ExactOut requested on EVM
                # unless we implement the specific 1inch endpoint.
                if swap_mode == "ExactOut":
                     raise BadRequestException("Exact Output swaps are currently optimized for Solana only.")
                     
                chain_id = self._get_evm_chain_id(chain)
                return await self._get_1inch_quote(
                    chain_id, token_in_address, token_out_address, amount_atomic, slippage_bps
                )
            else:
                raise BadRequestException(f"Swaps are not supported for chain: {chain}")
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error fetching swap quote for {chain}: {str(e)}")
            raise ServiceUnavailableException("DEX Aggregator", str(e))

    async def get_swap_instructions(
        self,
        chain: Chain,
        quote_response: Dict[str, Any],
        user_public_key: str
    ) -> Dict[str, Any]:
        try:
            if chain == Chain.SOLANA:
                return await self._get_jupiter_swap_instructions(quote_response, user_public_key)
            elif chain in [Chain.ETHEREUM, Chain.POLYGON, Chain.BASE]:
                chain_id = self._get_evm_chain_id(chain)
                return await self._get_1inch_swap_calldata(chain_id, quote_response, user_public_key)
            else:
                raise BadRequestException(f"Swaps not supported for chain: {chain}")
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error generating swap instructions: {str(e)}")
            raise ServiceUnavailableException("DEX Aggregator", str(e))

    async def _get_jupiter_quote(
        self, input_mint: str, output_mint: str, amount: int, slippage_bps: int, swap_mode: str
    ) -> Dict[str, Any]:
        # Jupiter v6 supports swapMode param
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
            "swapMode": swap_mode, 
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false" 
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.jupiter_api_url}/quote", params=params)
                if response.status_code != 200:
                    raise BadRequestException(f"Jupiter Quote Failed: {response.text}")
                
                data = response.json()
                return {
                    "aggregator": "Jupiter",
                    "chain": Chain.SOLANA,
                    "amount_in": int(data["inAmount"]),
                    "amount_out": int(data["outAmount"]),
                    "price_impact_pct": float(data.get("priceImpactPct", 0)),
                    "swap_mode": swap_mode,
                    "raw_quote": data
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("Jupiter API", str(e))

    async def _get_jupiter_swap_instructions(
        self, quote_response: Dict[str, Any], user_public_key: str
    ) -> Dict[str, Any]:
        payload = {
            "quoteResponse": quote_response["raw_quote"],
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.jupiter_api_url}/swap", json=payload)
                if response.status_code != 200:
                    raise BadRequestException(f"Jupiter Swap Failed: {response.text}")
                
                data = response.json()
                return {
                    # Base64 versioned transaction. Trust Wallet Core creates a signature 
                    # for this if using 'Sign Solana Message' or similar, but typically 
                    # TWC expects raw instructions to build the tx. 
                    # HOWEVER, standard Solana dApps sign the *transaction object*.
                    # The frontend must deserialize this base64 blob and sign it.
                    "swap_transaction": data["swapTransaction"], 
                    "last_valid_block_height": data.get("lastValidBlockHeight")
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("Jupiter API", str(e))

    async def _get_1inch_quote(
        self, chain_id: int, token_in: str, token_out: str, amount: int, slippage_bps: int
    ) -> Dict[str, Any]:
        fee_pct = slippage_bps / 100.0
        params = {
            "src": token_in,
            "dst": token_out,
            "amount": str(amount),
            "fee": fee_pct
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.oneinch_api_url}/{chain_id}/quote", params=params, headers=self.oneinch_headers)
                if response.status_code != 200:
                    raise BadRequestException(f"1inch Quote Failed: {response.text}")
                data = response.json()
                return {
                    "aggregator": "1inch",
                    "chain_id": chain_id,
                    "amount_in": int(data["toAmount"]), 
                    "amount_out": int(data["toAmount"]),
                    "raw_quote": data
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("1inch API", str(e))

    async def _get_1inch_swap_calldata(
        self, chain_id: int, quote_response: Dict[str, Any], user_address: str
    ) -> Dict[str, Any]:
        raw = quote_response["raw_quote"]
        params = {
            "src": raw["fromToken"]["address"],
            "dst": raw["toToken"]["address"],
            "amount": raw["fromTokenAmount"],
            "from": user_address,
            "slippage": 0.5,
            "disableEstimate": "true"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.oneinch_api_url}/{chain_id}/swap", params=params, headers=self.oneinch_headers)
                if response.status_code != 200:
                    raise BadRequestException(f"1inch Swap Failed: {response.text}")
                data = response.json()
                return {
                    "to": data["tx"]["to"],
                    "data": data["tx"]["data"],
                    "value": data["tx"]["value"],
                    "gas_limit": data["tx"]["gas"]
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("1inch API", str(e))

    def _get_evm_chain_id(self, chain: Chain) -> int:
        mapping = {Chain.ETHEREUM: 1, Chain.POLYGON: 137, Chain.BASE: 8453}
        if chain not in mapping:
            raise BadRequestException(f"Chain ID not configured for {chain}")
        return mapping[chain]

