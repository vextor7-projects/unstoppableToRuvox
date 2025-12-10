import logging
import httpx
from typing import List, Optional, Dict, Any

from app.core.config import settings
from app.utils.enums import Chain
from app.schemas.nft import NftMetadata, NftAttribute, NftBase
from app.utils.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)

class NftService:
    """
    Service for fetching NFT data.
    Integrates with Moral (EVM/Solana) or OpenSea API.
    """

    def __init__(self):
        # Placeholder URL - needs actual Moral/OpenSea Endpoint
        self.api_base_url = "https://deep-index.moralis.io/api/v2.2"
        self.api_key = settings.MORALIS_API_KEY if hasattr(settings, "MORALIS_API_KEY") else ""
        self.headers = {"X-API-Key": self.api_key}

    async def get_wallet_nfts(self, chain: Chain, address: str) -> List[NftMetadata]:
        """
        Fetch NFTs owned by a wallet address.
        """
        if not self.api_key:
            logger.warning("NFT API Key missing. Returning empty list.")
            return []

        chain_hex = self._get_chain_hex(chain)
        if not chain_hex:
             return [] # Unsupported chain for NFT API

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/{address}/nft",
                    params={"chain": chain_hex, "format": "decimal"},
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                nfts = []
                for item in data.get("result", []):
                    # Parse metadata (often stringified JSON)
                    meta_json = item.get("metadata")
                    meta_dict = {}
                    if meta_json:
                        try:
                            meta_dict = meta_json if isinstance(meta_json, dict) else import_json(meta_json)
                        except:
                            pass

                    nfts.append(NftMetadata(
                        name=meta_dict.get("name") or f"#{item.get('token_id')}",
                        description=meta_dict.get("description"),
                        image=self._resolve_ipfs(meta_dict.get("image")),
                        token_id=item.get("token_id"),
                        contract_address=item.get("token_address")
                    ))
                return nfts

        except Exception as e:
            logger.error(f"NFT Fetch Error: {e}")
            raise ServiceUnavailableException("NFT Data Provider")

    def _get_chain_hex(self, chain: Chain) -> Optional[str]:
        """Map internal Chain enum to Moralis chain params."""
        if chain == Chain.ETHEREUM: return "0x1"
        if chain == Chain.POLYGON: return "0x89"
        if chain == Chain.BASE: return "0x2105"
        if chain == Chain.SOLANA: return "solana" # Moralis uses separate endpoint for Sol usually
        return None

    def _resolve_ipfs(self, url: Optional[str]) -> Optional[str]:
        """Convert IPFS:// to a gateway HTTP URL."""
        if url and url.startswith("ipfs://"):
            return url.replace("ipfs://", "https://ipfs.io/ipfs/")
        return url

def import_json(j):
    import json
    return json.loads(j)