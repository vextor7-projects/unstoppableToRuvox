import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, AnyHttpUrl

from app.utils.enums import Chain

# --- NFT Metadata and Attributes Schemas ---

class NftAttribute(BaseModel):
    """ Schema for a single attribute (trait) of an NFT. """
    trait_type: Optional[str] = None
    value: Any # Can be string, number, etc.
    display_type: Optional[str] = None # OpenSea standard for how to display (e.g., 'number', 'boost_percentage')

class NftMetadata(BaseModel):
    """ Schema representing the metadata associated with an NFT. """
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[AnyHttpUrl] = None # Primary image URL
    external_url: Optional[AnyHttpUrl] = None # Link to project website or details page
    animation_url: Optional[AnyHttpUrl] = None # URL for video or animation
    attributes: Optional[List[NftAttribute]] = None

# --- NFT Representation Schemas ---

class NftBase(BaseModel):
    """ Base schema for core NFT information. """
    chain: Chain
    contract_address: str = Field(..., description="The address of the NFT contract (collection)")
    token_id: str = Field(..., description="The unique identifier of the NFT within its contract")
    standard: Optional[str] = Field(None, description="NFT standard (e.g., 'ERC721', 'ERC1155', 'Metaplex')")

    class ConfigDict:
        from_attributes = True # Allow creating schema from ORM model (if we store NFTs)

class Nft(NftBase):
    """
    Schema representing a complete NFT object, including metadata,
    returned by the API for display in the wallet.
    """
    owner_address: Optional[str] = Field(None, description="Current owner's address (fetched on demand)")
    metadata: Optional[NftMetadata] = Field(None, description="Parsed metadata for the NFT")
    # Add fields from marketplace integrations if needed (Stage 12)
    floor_price: Optional[Decimal] = Field(None, description="Collection floor price from marketplace")
    last_sale_price: Optional[Decimal] = Field(None, description="Last sale price from marketplace")
    collection_name: Optional[str] = Field(None, description="Name of the NFT collection")
    # Add other fields like rarity score if available

# --- NFT Transfer Schemas ---

class NftTransferPrepareRequest(BaseModel):
    """
    Schema for requesting the backend to prepare an NFT transfer transaction.
    Similar to token transfer, but specifies NFT details.
    """
    portfolio_id: uuid.UUID
    from_wallet_id: uuid.UUID # Source wallet ID owning the NFT
    to_address: str # Recipient wallet address
    
    # NFT Identification
    contract_address: str
    token_id: str
    chain: Chain
    standard: Optional[str] = Field(None, description="NFT standard (e.g., 'ERC721', 'ERC1155') - helps backend")

    # Optional fee level preference
    fee_level: Optional[str] = Field("medium", pattern="^(slow|medium|fast)$")

# NftTransferPrepareResponse would be similar to TransactionPrepareResponse,
# containing the unsigned transaction data specific to the NFT transfer function call.
# Use a generic structure or define a specific one if needed.
# from app.schemas.transaction import TransactionPrepareResponse as NftTransferPrepareResponse

# NftTransferBroadcastRequest would be similar to TransactionBroadcastRequest,
# submitting the signed NFT transfer transaction.
# from app.schemas.transaction import TransactionBroadcastRequest as NftTransferBroadcastRequest

# NftTransferBroadcastResponse would be similar to TransactionBroadcastResponse,
# providing the tx_hash of the NFT transfer.
# from app.schemas.transaction import TransactionBroadcastResponse as NftTransferBroadcastResponse
