import httpx
import json
from typing import Any, Dict, Optional, List, Union

from app.core.config import settings
from app.utils.enums import Chain
from app.utils.exceptions import RpcNodeException

class RpcClient:
    """
    Unified client for JSON-RPC calls.
    Handles broadcasting logic for different chains.
    """

    def __init__(self):
        self.rpc_urls = {
            Chain.SOLANA: str(settings.SOLANA_RPC_URL),
            Chain.BASE: str(settings.BASE_RPC_URL),
            Chain.POLYGON: str(settings.POLYGON_RPC_URL),
            Chain.ETHEREUM: str(settings.ETHEREUM_RPC_URL),
            Chain.BITCOIN: str(getattr(settings, "BITCOIN_RPC_URL", "")),
        }
        
        # Devnet overrides
        if settings.ENVIRONMENT == "development":
            if settings.SOLANA_DEVNET_RPC_URL:
                self.rpc_urls[Chain.SOLANA] = str(settings.SOLANA_DEVNET_RPC_URL)
            if settings.BASE_SEPOLIA_RPC_URL:
                self.rpc_urls[Chain.BASE] = str(settings.BASE_SEPOLIA_RPC_URL)
            if settings.POLYGON_MUMBAI_RPC_URL:
                self.rpc_urls[Chain.POLYGON] = str(settings.POLYGON_MUMBAI_RPC_URL)
            if settings.ETHEREUM_SEPOLIA_RPC_URL:
                self.rpc_urls[Chain.ETHEREUM] = str(settings.ETHEREUM_SEPOLIA_RPC_URL)

    async def make_request(
        self, 
        chain: Chain, 
        method: str, 
        params: list = [], 
        id: int = 1
    ) -> Any:
        url = self.rpc_urls.get(chain)
        if not url:
            raise RpcNodeException(detail=f"No RPC URL configured for {chain}.")

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": id
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown RPC error")
                    raise RpcNodeException(detail=f"RPC Error on {chain}: {error_msg}")
                
                return data.get("result")
                
        except httpx.RequestError as e:
            raise RpcNodeException(detail=f"Failed to connect to {chain} node: {str(e)}")
        except Exception as e:
            raise RpcNodeException(detail=f"Unexpected error on {chain}: {str(e)}")

    async def send_raw_transaction(self, chain: Chain, signed_tx: str) -> str:
        """
        Broadcast a signed transaction string to the network.
        Returns the Transaction Hash.
        """
        method = ""
        params = []

        if chain == Chain.SOLANA:
            # Solana: sendTransaction. params: [base64_string, {encoding: base64}]
            method = "sendTransaction"
            params = [signed_tx, {"encoding": "base64"}]
            
        elif chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            # EVM: eth_sendRawTransaction. params: [hex_string]
            method = "eth_sendRawTransaction"
            # Ensure 0x prefix for EVM
            if not signed_tx.startswith("0x"):
                signed_tx = f"0x{signed_tx}"
            params = [signed_tx]
            
        elif chain == Chain.BITCOIN:
            # Bitcoin: sendrawtransaction. params: [hex_string]
            method = "sendrawtransaction"
            params = [signed_tx]
            
        else:
            raise NotImplementedError(f"Broadcast not implemented for {chain}")

        # Execute
        tx_hash = await self.make_request(chain, method, params)
        return str(tx_hash)

    async def get_balance(self, chain: Chain, address: str) -> int:
        """
        Helper to get native balance (wei/lamports).
        """
        if chain == Chain.SOLANA:
            result = await self.make_request(chain, "getBalance", [address])
            if isinstance(result, dict) and "value" in result:
                return result["value"]
            return 0
        elif chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            result = await self.make_request(chain, "eth_getBalance", [address, "latest"])
            return int(result, 16)
        else:
            return 0

rpc_client = RpcClient()