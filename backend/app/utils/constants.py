import re
from decimal import Decimal

# --- User and Security Constants ---

# Regex for validating usernames. Must start with '@' and contain 3-20 alphanumeric chars/underscores.
USERNAME_REGEX = re.compile(r"^@[a-zA-Z0-9_]{3,20}$")

# Regex for validating a 6-digit numeric PIN.
PIN_REGEX = re.compile(r"^\d{6}$")

# Number of TOTP backup codes to generate.
TOTP_BACKUP_CODE_COUNT = 10

# Length of each backup code.
TOTP_BACKUP_CODE_DIGITS = 8

# Maximum login/PIN attempts before temporary lockout.
MAX_AUTH_ATTEMPTS = 5


# --- Transaction and Compliance Constants ---

# Travel Rule threshold in USD (as per Stage 10).
TRAVEL_RULE_THRESHOLD_USD = Decimal("3000.00")

# Default slippage tolerance for swaps (0.5% as per Stage 2).
SLIPPAGE_TOLERANCE_DEFAULT = Decimal("0.005") # 0.5%

# Number of confirmations required for crediting deposits (as per Stage 5).
CONFIRMATION_THRESHOLDS = {
    "SOLANA": 32,
    "BASE": 12,
    "POLYGON": 12,
    "ETHEREUM": 12,
    "BITCOIN": 3, # 3 confirmations for BTC is a common standard
}


# --- Payment Constants ---

# Expiry time for a QR/NFC payment session in minutes (as per Stage 8).
PAYMENT_SESSION_EXPIRY_MINUTES = 5


# --- KYC Transfer Limits (as per Stage 3) ---
# Daily transfer limits in USD equivalent based on KYC level.
KYC_TRANSFER_LIMITS_USD = {
    "not_started": Decimal("0.00"),
    "approved_level_1": Decimal("1000.00"),    # Example: Email/SMS verified
    "approved_level_2": Decimal("10000.00"),   # Example: ID verified
    "approved_level_3": Decimal("100000.00"),  # Example: Address verified
    "rejected": Decimal("0.00"),
}


# --- General Application Constants ---

# Standard precision for monetary values (e.g., USD).
USD_DECIMAL_PRECISION = 2

# Standard precision for cryptocurrency amounts.
CRYPTO_DECIMAL_PRECISION = 18 # High precision for calculations

# Default page size for pagination.
DEFAULT_PAGINATION_LIMIT = 20

# Maximum page size for pagination.
MAX_PAGINATION_LIMIT = 100
