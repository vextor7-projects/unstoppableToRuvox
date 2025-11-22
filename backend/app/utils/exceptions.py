from typing import Optional, Dict, Any

class AppException(Exception):
    """
    Base exception class for the application.
    All custom exceptions should inherit from this.
    
    Attributes:
        status_code (int): The HTTP status code to return.
        detail (str): A user-friendly error message.
        headers (Optional[Dict[str, Any]]): Optional headers to include in the response.
    """
    def __init__(
        self,
        status_code: int = 500,
        detail: str = "An internal server error occurred.",
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(self.detail)


# --- Authentication / Authorization Errors (401, 403) ---

class InvalidCredentialsException(AppException):
    """Raised when authentication fails (e.g., wrong username/PIN)."""
    def __init__(
        self,
        detail: str = "Incorrect email, username, or PIN.",
        headers: Optional[Dict[str, Any]] = {"WWW-Authenticate": "Bearer"},
    ):
        super().__init__(status_code=401, detail=detail, headers=headers)

class TokenExpiredException(AppException):
    """Raised when a JWT token has expired."""
    def __init__(
        self,
        detail: str = "Token has expired.",
        headers: Optional[Dict[str, Any]] = {"WWW-Authenticate": "Bearer"},
    ):
        super().__init__(status_code=401, detail=detail, headers=headers)

class InvalidTokenException(AppException):
    """Raised when a JWT token is invalid (e.g., bad signature)."""
    def __init__(
        self,
        detail: str = "Invalid authentication token.",
        headers: Optional[Dict[str, Any]] = {"WWW-Authenticate": "Bearer"},
    ):
        super().__init__(status_code=401, detail=detail, headers=headers)

class NotAuthorizedException(AppException):
    """Raised when a user is authenticated but not permitted to perform an action."""
    def __init__(
        self,
        detail: str = "You do not have permission to perform this action.",
    ):
        super().__init__(status_code=403, detail=detail)

class AdminRequiredException(NotAuthorizedException):
    """Raised when a non-admin user attempts an admin-only action."""
    def __init__(
        self,
        detail: str = "Administrator privileges are required.",
    ):
        super().__init__(detail=detail)

class MerchantRequiredException(NotAuthorizedException):
    """Raised when a non-merchant user attempts a merchant-only action."""
    def __init__(
        self,
        detail: str = "A verified merchant account is required.",
    ):
        super().__init__(detail=detail)


# --- Not Found Errors (404) ---

class NotFoundException(AppException):
    """Base class for 404 errors."""
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=404, detail=detail)

class UserNotFoundException(NotFoundException):
    """Raised when a user is not found in the database."""
    def __init__(self, detail: str = "User not found."):
        super().__init__(detail=detail)

class WalletNotFoundException(NotFoundException):
    """Raised when a wallet or portfolio is not found."""
    def __init__(self, detail: str = "Wallet or portfolio not found."):
        super().__init__(detail=detail)

class TransactionNotFoundException(NotFoundException):
    """Raised when a transaction is not found."""
    def __init__(self, detail: str = "Transaction not found."):
        super().__init__(detail=detail)

class InvoiceNotFoundException(NotFoundException):
    """Raised when an invoice is not found."""
    def __init__(self, detail: str = "Invoice not found."):
        super().__init__(detail=detail)

class PaymentSessionNotFoundException(NotFoundException):
    """Raised when a payment session is not found or expired."""
    def __init__(self, detail: str = "Payment session not found or expired."):
        super().__init__(detail=detail)


# --- Conflict / Bad Request Errors (400, 409) ---

class BadRequestException(AppException):
    """Base class for 400 errors."""
    def __init__(self, detail: str = "Bad request."):
        super().__init__(status_code=400, detail=detail)

class ConflictException(AppException):
    """Base class for 409 errors."""
    def __init__(self, detail: str = "Resource conflict."):
        super().__init__(status_code=409, detail=detail)

class EmailAlreadyExistsException(ConflictException):
    """Raised during registration if the email is already taken."""
    def __init__(self, detail: str = "This email address is already registered."):
        super().__init__(detail=detail)

class UsernameAlreadyExistsException(ConflictException):
    """Raised during registration if the username is already taken."""
    def __init__(self, detail: str = "This username is already taken."):
        super().__init__(detail=detail)

class InvalidPinException(BadRequestException):
    """Raised when a PIN does not meet validation criteria."""
    def __init__(self, detail: str = "Invalid PIN. Must be 6 digits."):
        super().__init__(detail=detail)

class InvalidTotpCodeException(BadRequestException):
    """Raised when a 2FA code is invalid."""
    def __init__(self, detail: str = "Invalid 2FA code."):
        super().__init__(detail=detail)

class KycLevelException(NotAuthorizedException):
    """Raised when a user's KYC level is insufficient for an action."""
    def __init__(
        self,
        required_level: int,
        detail: str = "Your current KYC level is not sufficient for this action.",
    ):
        self.required_level = required_level
        super().__init__(detail=f"{detail} Required level: {required_level}.")

class ComplianceException(AppException):
    """Raised when a transaction is blocked by compliance (e.g., Chainalysis)."""
    def __init__(
        self,
        detail: str = "This action was blocked for compliance reasons.",
    ):
        super().__init__(status_code=403, detail=detail)


# --- Blockchain / Wallet Errors (400, 500) ---

class InsufficientBalanceException(BadRequestException):
    """Raised when on-chain or internal ledger balance is too low."""
    def __init__(self, detail: str = "Insufficient balance for this transaction."):
        super().__init__(detail=detail)

class TransactionFailedException(AppException):
    """Raised when a blockchain transaction fails to broadcast or confirm."""
    def __init__(self, detail: str = "Blockchain transaction failed."):
        super().__init__(status_code=500, detail=detail)

class RpcNodeException(AppException):
    """Raised when a connection to a blockchain RPC node fails."""
    def __init__(self, detail: str = "Cannot connect to blockchain network. Please try again later."):
        super().__init__(status_code=503, detail=detail)

class InvalidAddressException(BadRequestException):
    """Raised when a blockchain address is not valid for the specified chain."""
    def __init__(self, detail: str = "Invalid wallet address."):
        super().__init__(detail=detail)


# --- Service Errors (500, 503) ---

class ServiceUnavailableException(AppException):
    """Raised when a third-party service (e.g., CoinGecko, AWS) is down."""
    def __init__(self, service_name: str, detail: Optional[str] = None):
        if not detail:
            detail = f"{service_name} service is currently unavailable. Please try again later."
        super().__init__(status_code=503, detail=detail)

class InternalLedgerException(AppException):
    """Raised for critical errors in the internal ledger (e.g., debits != credits)."""
    def __init__(self, detail: str = "An internal accounting error occurred. Please contact support."):
        super().__init__(status_code=500, detail=detail)

class EncryptionException(AppException):
    """Raised if data encryption or decryption fails."""
    def __init__(self, detail: str = "A security error occurred while processing your data."):
        super().__init__(status_code=500, detail=detail)
