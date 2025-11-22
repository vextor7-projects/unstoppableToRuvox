from enum import Enum

class UserRole(str, Enum):
    """Enumeration for user roles."""
    USER = "user"
    MERCHANT = "merchant"
    ADMIN = "admin"

class Chain(str, Enum):
    """
    Enumeration for supported blockchain networks.
    Values should be consistent and simple.
    """
    SOLANA = "SOLANA"
    BASE = "BASE"
    POLYGON = "POLYGON"
    ETHEREUM = "ETHEREUM"
    BITCOIN = "BITCOIN"

class KycStatus(str, Enum):
    """Enumeration for KYC submission statuses."""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    APPROVED_LEVEL_1 = "approved_level_1"
    APPROVED_LEVEL_2 = "approved_level_2"
    APPROVED_LEVEL_3 = "approved_level_3"
    REJECTED = "rejected"

class TransactionStatus(str, Enum):
    """Enumeration for on-chain and off-chain transaction statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TransactionType(str, Enum):
    """Enumeration for on-chain transaction types."""
    SEND = "send"
    RECEIVE = "receive"
    SWAP = "swap"
    PAYMENT = "payment"
    STAKE = "stake"
    UNSTAKE = "unstake"
    APPROVE = "approve" # For token approvals
    OTHER = "other"

class LedgerTransactionType(str, Enum):
    """Enumeration for internal double-entry ledger transaction types."""
    DEPOSIT = "deposit"               # On-chain deposit to hot wallet
    WITHDRAWAL = "withdrawal"         # Off-chain withdrawal from internal account
    ONRAMP_PURCHASE = "onramp_purchase" # Fiat on-ramp purchase
    INTERNAL_TRANSFER = "internal_transfer" # User-to-user instant transfer
    MERCHANT_PAYMENT = "merchant_payment" # Payment to a merchant
    STAKING_REWARD = "staking_reward"   # Interest payment
    FEE = "fee"                       # Service fee collection
    SETTLEMENT = "settlement"         # Merchant settlement payout

class PaymentSessionStatus(str, Enum):
    """Enumeration for QR/NFC payment session statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"

class InvoiceStatus(str, Enum):
    """Enumeration for invoice statuses."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class SubscriptionStatus(str, Enum):
    """Enumeration for recurring payment subscription statuses."""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed" # For subscriptions with a fixed number of cycles

class PullPaymentStatus(str, Enum):
    """Enumeration for pull payment approval statuses."""
    ACTIVE = "active"
    PAUSED = "paused"
    REVOKED = "revoked"

class VipTier(str, Enum):
    """Enumeration for VIP tiers."""
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

class ComplianceAction(str, Enum):
    """Enumeration for blockchain screening results."""
    ALLOW = "allow"
    DENY = "deny"
    FLAG_FOR_REVIEW = "flag_for_review"
    REQUIRE_ADDITIONAL_INFO = "require_additional_info"