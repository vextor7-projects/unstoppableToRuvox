import httpx
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from app.core.config import settings
from app.utils.enums import Chain
from app.utils.constants import SLIPPAGE_TOLERANCE_DEFAULT
from app.utils.exceptions import (
    ServiceUnavailableException, 
    BadRequestException,
    AppException
)

# Configure logger
logger = logging.getLogger(__name__)

class DexAggregatorService:
    """
    Service to interact with DEX aggregators (Jupiter for Solana, 1inch for EVM).
    Standardizes quotes and swap data retrieval across different chains.
    
    This service is designed to be stateless regarding the database, but follows
    the project pattern of Service instantiation.
    """

    def __init__(self):
        # Base URLs for APIs
        self.jupiter_api_url = "https://quote-api.jup.ag/v6"
        self.oneinch_api_url = "https://api.1inch.dev/swap/v5.2"
        
        # 1inch requires an API key in headers
        self.oneinch_headers = {
            "Authorization": f"Bearer {settings.ONEINCH_API_KEY}"
        } if hasattr(settings, "ONEINCH_API_KEY") and settings.ONEINCH_API_KEY else {}

    async def get_quote(
        self,
        chain: Chain,
        token_in_address: str,
        token_out_address: str,
        amount_in_atomic: int,
        slippage_bps: int = int(SLIPPAGE_TOLERANCE_DEFAULT * 10000) # e.g., 0.5% -> 50 bps
    ) -> Dict[str, Any]:
        """
        Get a swap quote from the appropriate aggregator based on the chain.
        
        :param chain: The blockchain network.
        :param token_in_address: Contract address of input token (or mint for Solana).
        :param token_out_address: Contract address of output token.
        :param amount_in_atomic: Amount in smallest unit (e.g., satoshis/wei).
        :param slippage_bps: Slippage tolerance in basis points.
        :return: Standardized quote dictionary used by the frontend or PaymentService.
        """
        try:
            if chain == Chain.SOLANA:
                return await self._get_jupiter_quote(
                    token_in_address, token_out_address, amount_in_atomic, slippage_bps
                )
            elif chain in [Chain.ETHEREUM, Chain.POLYGON, Chain.BASE, Chain.BNB]:
                chain_id = self._get_evm_chain_id(chain)
                return await self._get_1inch_quote(
                    chain_id, token_in_address, token_out_address, amount_in_atomic, slippage_bps
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
        """
        Get the binary/instruction data to build the swap transaction.
        This is called after the user approves the quote.
        """
        try:
            if chain == Chain.SOLANA:
                return await self._get_jupiter_swap_instructions(quote_response, user_public_key)
            elif chain in [Chain.ETHEREUM, Chain.POLYGON, Chain.BASE, Chain.BNB]:
                chain_id = self._get_evm_chain_id(chain)
                return await self._get_1inch_swap_calldata(chain_id, quote_response, user_public_key)
            else:
                raise BadRequestException(f"Swaps not supported for chain: {chain}")
                
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error generating swap instructions for {chain}: {str(e)}")
            raise ServiceUnavailableException("DEX Aggregator", str(e))

    # --- Solana (Jupiter) Implementation ---

    async def _get_jupiter_quote(
        self, input_mint: str, output_mint: str, amount: int, slippage_bps: int
    ) -> Dict[str, Any]:
        """
        Fetch quote from Jupiter Aggregator (Solana).
        """
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false" # We prefer Versioned Transactions (V0)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.jupiter_api_url}/quote", params=params)
                
                if response.status_code != 200:
                    error_detail = response.json().get("error", response.text)
                    raise BadRequestException(f"Jupiter Quote Failed: {error_detail}")
                
                data = response.json()
                
                # Standardized response format
                return {
                    "aggregator": "Jupiter",
                    "chain": Chain.SOLANA,
                    "amount_in": int(data["inAmount"]),
                    "amount_out": int(data["outAmount"]),
                    "price_impact_pct": float(data.get("priceImpactPct", 0)),
                    "raw_quote": data # Store raw data to pass back for swap generation
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("Jupiter API", str(e))

    async def _get_jupiter_swap_instructions(
        self, quote_response: Dict[str, Any], user_public_key: str
    ) -> Dict[str, Any]:
        """
        Get serialized transaction payload from Jupiter.
        """
        payload = {
            "quoteResponse": quote_response["raw_quote"],
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            # Optional: feeAccount (if we want to collect app fees)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.jupiter_api_url}/swap", json=payload)
                
                if response.status_code != 200:
                    error_detail = response.json().get("error", response.text)
                    raise BadRequestException(f"Jupiter Swap Failed: {error_detail}")
                
                data = response.json()
                
                return {
                    "swap_transaction": data["swapTransaction"], # Base64 encoded Versioned Transaction
                    "last_valid_block_height": data.get("lastValidBlockHeight")
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("Jupiter API", str(e))

    # --- EVM (1inch) Implementation ---

    async def _get_1inch_quote(
        self, chain_id: int, token_in: str, token_out: str, amount: int, slippage_bps: int
    ) -> Dict[str, Any]:
        """
        Fetch quote from 1inch Aggregator (EVM).
        """
        # 1inch uses fee percentage (e.g., 1 = 1%), so bps 50 = 0.5
        fee_pct = slippage_bps / 100.0
        
        params = {
            "src": token_in,
            "dst": token_out,
            "amount": str(amount),
            "fee": fee_pct,
            "includeTokensInfo": "true",
            "includeProtocols": "true"
        }

        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.oneinch_api_url}/{chain_id}/quote"
                response = await client.get(url, params=params, headers=self.oneinch_headers)
                
                if response.status_code != 200:
                    # 1inch errors often come with description
                    error_msg = response.json().get("description", response.text)
                    raise BadRequestException(f"1inch Quote Failed: {error_msg}")
                
                data = response.json()
                
                return {
                    "aggregator": "1inch",
                    "chain_id": chain_id,
                    "amount_in": int(data["toAmount"]), # Note: 1inch naming can be tricky, check specifics
                    "amount_out": int(data["toAmount"]),
                    "price_impact_pct": 0.0, # 1inch quote endpoint typically doesn't return impact, swap does
                    "raw_quote": data
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("1inch API", str(e))

    async def _get_1inch_swap_calldata(
        self, chain_id: int, quote_response: Dict[str, Any], user_address: str
    ) -> Dict[str, Any]:
        """
        Get calldata for 1inch router.
        """
        raw = quote_response["raw_quote"]
        
        # 1inch /swap endpoint generates the calldata
        # We rely on the previous quote data to populate this request
        params = {
            "src": raw["fromToken"]["address"],
            "dst": raw["toToken"]["address"],
            "amount": raw["fromTokenAmount"],
            "from": user_address,
            "slippage": 0.5, # Should match the quote's slippage
            "disableEstimate": "true" # We estimate gas separately in TransactionService
        }

        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.oneinch_api_url}/{chain_id}/swap"
                response = await client.get(url, params=params, headers=self.oneinch_headers)
                
                if response.status_code != 200:
                    error_msg = response.json().get("description", response.text)
                    raise BadRequestException(f"1inch Swap Failed: {error_msg}")
                
                data = response.json()
                
                return {
                    "to": data["tx"]["to"],
                    "data": data["tx"]["data"],
                    "value": data["tx"]["value"],
                    "gas_limit": data["tx"]["gas"] # 1inch estimation
                }
            except httpx.RequestError as e:
                raise ServiceUnavailableException("1inch API", str(e))

    def _get_evm_chain_id(self, chain: Chain) -> int:
        """Map app Chain enum to EVM Chain IDs."""
        mapping = {
            Chain.ETHEREUM: 1,
            Chain.POLYGON: 137,
            Chain.BASE: 8453,
            # Chain.BNB: 56 # If BNB is supported in future
        }
        if chain not in mapping:
            raise BadRequestException(f"Chain ID not configured for {chain}")
        return mapping[chain]