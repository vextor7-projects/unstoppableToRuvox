from enum import Enum

class UserRole(str, Enum):
    """Enumeration for user roles."""
    USER = "user"
    MERCHANT = "merchant"
    ADMIN = "admin"

class UserStatus(str, Enum):
    """Enumeration for user account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LOCKED = "locked"

class Chain(str, Enum):
    """
    Enumeration for supported blockchain networks.
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
    NOT_VERIFIED = "not_verified"
    SUBMITTED = "submitted"

class KycLevel(str, Enum):
    """Enumeration for KYC levels."""
    NOT_STARTED = "not_started"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"

class TransactionStatus(str, Enum):
    """Enumeration for general transaction statuses."""
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
    APPROVE = "approve"
    OTHER = "other"

class LedgerEntryType(str, Enum):
    """Enumeration for internal double-entry ledger transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ONRAMP_PURCHASE = "onramp_purchase"
    INTERNAL_TRANSFER = "internal_transfer"
    MERCHANT_PAYMENT = "merchant_payment"
    STAKING_REWARD = "staking_reward"
    FEE = "fee"
    SETTLEMENT = "settlement"

class DepositStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class WithdrawalStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

class ComplianceCheckStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"

class PaymentSessionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"

class PaymentType(str, Enum):
    """Enumeration for payment methods."""
    QR_CODE = "qr_code"
    NFC = "nfc"
    PAYMENT_LINK = "payment_link"
    MANUAL = "manual"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    PENDING = "pending"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class SubscriptionFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class PullPaymentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    REVOKED = "revoked"

class VipTierLevel(str, Enum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

class ComplianceStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ScreeningAction(str, Enum):
    ALLOWED = "allowed"
    FLAG_FOR_REVIEW = "flag_for_review"
    BLOCKED = "blocked"

class SuspiciousActivityStatus(str, Enum):
    FLAGGED = "flagged"
    RESOLVED = "resolved"
    CONFIRMED_FRAUD = "confirmed_fraud"
    FALSE_POSITIVE = "false_positive"

class ReportType(str, Enum):
    SAR = "suspicious_activity_report"
    CTR = "currency_transaction_report"
    TRAVEL_RULE = "travel_rule"

class ReportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class PriceAlertDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"

class PriceAlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    INACTIVE = "inactive"

class SmartContractType(str, Enum):
    PAYMENT_ROUTER = "payment_router"
    STAKING_POOL = "staking_pool"
    ESCROW = "escrow"

class SettlementStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SettlementFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class MerchantEmployeeRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"

class ComplianceAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    FLAG_FOR_REVIEW = "flag_for_review"
    REQUIRE_ADDITIONAL_INFO = "require_additional_info"