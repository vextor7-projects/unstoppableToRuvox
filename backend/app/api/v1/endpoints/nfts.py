from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.schemas.nft import NftMetadata
from app.services.nft_service import NftService
from app.utils.enums import Chain
from app.utils.exceptions import ServiceUnavailableException

router = APIRouter()

@router.get("/{address}", response_model=List[NftMetadata])
async def get_nfts(
    address: str,
    chain: Chain = Query(..., description="Chain to fetch NFTs from"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get NFTs for a specific wallet address.
    """
    service = NftService()
    try:
        return await service.get_wallet_nfts(chain, address)
    except ServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))