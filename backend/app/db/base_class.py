import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, mapped_column


@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models.
    
    Includes an auto-generating UUID primary key, `created_at`, 
    and `updated_at` columns.
    
    It also automatically generates table names based on the class name.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc)
    )

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Converts CamelCase class name to snake_case table name.
        Example: 'KycSubmission' -> 'kyc_submission'
        """
        import re
        
        # This regex will insert an underscore before any capital letter
        # except for the very first letter of the string.
        # It handles acronyms as well (e.g., BitcoinUTXO -> bitcoin_utxo).
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
