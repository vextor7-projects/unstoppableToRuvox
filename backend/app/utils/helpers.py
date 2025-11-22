import secrets
import string
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.utils.constants import (
    USD_DECIMAL_PRECISION,
    TOTP_BACKUP_CODE_DIGITS,
    TOTP_BACKUP_CODE_COUNT,
)

def generate_unique_id(prefix: str = "") -> str:
    """
    Generates a unique, prefixed ID using UUIDv4.
    e.g., "inv_a1b2c3d4e5f6"
    """
    return f"{prefix}{uuid.uuid4().hex}"

def generate_secure_random_string(length: int) -> str:
    """
    Generates a cryptographically secure random string of a given length.
    Used for generating secrets or tokens.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def generate_numeric_otp_string(length: int) -> str:
    """
    Generates a cryptographically secure random numeric string (OTP).
    """
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def generate_totp_backup_codes() -> list[str]:
    """
    Generates a list of secure backup codes for 2FA.
    """
    codes = [
        generate_numeric_otp_string(TOTP_BACKUP_CODE_DIGITS)
        for _ in range(TOTP_BACKUP_CODE_COUNT)
    ]
    return codes

def format_decimal_to_usd_string(amount: Decimal) -> str:
    """
    Formats a Decimal amount into a standard USD string representation
    with two decimal places.
    
    Example: Decimal("123.456") -> "123.46"
    """
    # Create the quantizer for 2 decimal places
    quantizer = Decimal(f"1e-{USD_DECIMAL_PRECISION}") # Equivalent to Decimal("0.01")
    
    # Use quantize to round to 2 decimal places (default rounding is ROUND_HALF_EVEN)
    return str(amount.quantize(quantizer))

def get_utc_now() -> datetime:
    """
    Returns the current datetime in UTC with timezone info.
    """
    return datetime.now(timezone.utc)

def calculate_percentage(
    total_amount: Decimal, 
    percentage: Decimal
) -> Decimal:
    """
    Calculates a percentage of a Decimal amount.
    `percentage` should be provided as a decimal (e.g., 0.01 for 1%).
    """
    return total_amount * percentage
