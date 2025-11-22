import uuid
from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    DateTime,
    Text,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.utils.enums import Chain, SmartContractType


class SmartContract(Base):
    """
    Stores addresses and ABIs for deployed smart contracts.
    (Stage 2)
    """
    __tablename__ = "smart_contract"

    chain = Column(Enum(Chain), nullable=False, index=True, primary_key=True)
    
    contract_type = Column(
        Enum(SmartContractType), 
        nullable=False, 
        index=True, 
        primary_key=True
    )
    
    address = Column(String(255), nullable=False, index=True)
    
    version = Column(Integer, default=1, nullable=False, primary_key=True)
    
    # The ABI (Application Binary Interface) of the contract,
    # encrypted for security and to save space if large.
    abi_encrypted = Column(Text, nullable=True)
    
    deployment_date = Column(DateTime(timezone=True), server_default=func.now())
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # --- Relationships ---
    
    # A single smart contract can be associated with many payment transactions
    payment_transactions = relationship(
        "PaymentTransaction", 
        back_populates="smart_contract"
    )
