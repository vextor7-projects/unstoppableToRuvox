from typing import Optional
from pydantic import BaseModel, Field

class IdempotencyMixin(BaseModel):
    """
    Mixin to add idempotency key to mutation requests.
    Critical for financial APIs to prevent double-processing on network retries.
    """
    idempotency_key: str = Field(
        ..., 
        min_length=10, 
        max_length=100, 
        description="Unique client-generated key to prevent duplicate operations."
    )