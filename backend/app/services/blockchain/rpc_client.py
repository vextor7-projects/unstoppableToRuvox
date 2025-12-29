import httpx
from typing import Any, Dict, Optional, List
from app.core.config import settings
from app.utils.enums import Chain
from app.utils.exceptions import RpcNodeException

class RpcClient:
    """
    Unified client for JSON-RPC calls with persistent connection pooling.
    """
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self):
        self.rpc_urls = {
            Chain.SOLANA: str(settings.SOLANA_RPC_URL),
            Chain.BASE: str(settings.BASE_RPC_URL),
            Chain.POLYGON: str(settings.POLYGON_RPC_URL),
            Chain.ETHEREUM: str(settings.ETHEREUM_RPC_URL),
            Chain.BITCOIN: str(getattr(settings, "BITCOIN_RPC_URL", "") or ""),
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

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Singleton pattern for AsyncClient to reuse connections."""
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=100))
        return cls._client

    async def close(self):
        """Cleanup method to be called on app shutdown."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def make_request(self, chain: Chain, method: str, params: list = [], id: int = 1) -> Any:
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
            client = self.get_client()
            response = await client.post(url, json=payload)
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
        method = ""
        params = []

        if chain == Chain.SOLANA:
            method = "sendTransaction"
            params = [signed_tx, {"encoding": "base64"}]
        elif chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            method = "eth_sendRawTransaction"
            if not signed_tx.startswith("0x"):
                signed_tx = f"0x{signed_tx}"
            params = [signed_tx]
        elif chain == Chain.BITCOIN:
            method = "sendrawtransaction"
            params = [signed_tx]
        else:
            raise NotImplementedError(f"Broadcast not implemented for {chain}")

        tx_hash = await self.make_request(chain, method, params)
        return str(tx_hash)

    async def get_balance(self, chain: Chain, address: str) -> int:
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