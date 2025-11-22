"""
SQLAlchemy Models Package

This __init__.py file imports all models from their respective modules
into the 'app.models' namespace.

This allows Alembic to easily discover all models for autogeneration of
migrations when it imports `Base.metadata` from `app.db.base_class`.

It also makes it simpler to import models elsewhere in the application,
e.g.: `from app.models import User, Wallet`
"""

# Import the Base class which all models inherit from
from app.db.base_class import Base

# Import all models
from .user import User, UserSecurity
from .kyc import KycSubmission
from .wallet import Portfolio, Wallet, TokenBalance, Transaction, BitcoinUtxo
from .ledger import InternalLedger, DepositTransaction, WithdrawalRequest
from .payment import (
    PaymentSession,
    PaymentTransaction,
    SwapTransaction,
    FeeDistribution,
)
from .invoice import Invoice
from .subscription import Subscription, PullPaymentApproval
from .merchant import (
    Merchant,
    MerchantKyc,
    MerchantSettlement,
    SettlementDetail,
    MerchantEmployee,
    MerchantTerminal,
)
from .staking_vip import (
    StakingPosition,
    InterestAccrual,
    VipTier,
    VipBenefitsLog,
    TierHistory,
)
from .compliance import (
    TravelRuleRecord,
    BlockchainScreening,
    SuspiciousActivity,
    ComplianceReport,
    RegulatorySubmission,
    MsbLicense,
)
from .market import PriceAlert, PriceSnapshot
from .smart_contract import SmartContract
