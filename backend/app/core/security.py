import pyotp
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, Union, List

import base64
import hashlib

import os
from cryptography.fernet import Fernet
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings




# -----------------------------------------------------------------------------
# 1. PIN / Password Hashing (passlib)
# -----------------------------------------------------------------------------

# Use bcrypt as it is strong and recommended for passwords/PINs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

# -----------------------------------------------------------------------------
# 2. JSON Web Tokens (JWT) (python-jose)
# -----------------------------------------------------------------------------

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Creates a new JWT Refresh Token.
    
    :param subject: The subject of the token (e.g., user ID).
    :return: A signed JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes a JWT token.
    
    :param token: The JWT string to decode.
    :return: The token payload as a dictionary, or None if validation fails.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# -----------------------------------------------------------------------------
# 3. Time-based One-Time Password (TOTP) (pyotp)
# -----------------------------------------------------------------------------

def generate_totp_secret() -> str:
    """Generates a new, base32-encoded secret key for TOTP."""
    return pyotp.random_base32()

def generate_totp_provisioning_uri(secret: str, email: str, issuer: str = "Ruvox") -> str:
    """
    Generates the provisioning URI for a TOTP authenticator app (like Google Authenticator).
    
    :param secret: The user's base32 TOTP secret.
    :param email: The user's email or identifier.
    :param issuer: The name of the application.
    :return: A provisioning URI string.
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verifies a user-provided TOTP code against the secret.
    
    :param secret: The user's base32 TOTP secret.
    :param code: The 6-digit code from the authenticator app.
    :return: True if the code is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def generate_totp_backup_codes(num_codes: int = 10, num_digits: int = 8) -> List[str]:
    """
    Generates a list of random backup codes.
    These must be hashed and stored securely in the database.
    
    :param num_codes: The number of codes to generate.
    :param num_digits: The length of each code.
    :return: A list of plain-text backup codes.
    """
    return [pyotp.random_base32(length=num_digits) for _ in range(num_codes)]


# -----------------------------------------------------------------------------
# 4. Data Encryption (cryptography - Fernet)
# -----------------------------------------------------------------------------

# We will use the SECRET_KEY for this. For production, it's better to use
# a dedicated, rotated key (like the KMS_KEY_ID from settings), but
# Fernet requires a 32-byte URL-safe base64-encoded key.
# For simplicity in this plan, we'll derive a key from the SECRET_KEY.
# A more robust solution would use AWS KMS for envelope encryption.

# This is a simplified implementation using the app's SECRET_KEY.
# In a real production system (as per Stage 3), we would integrate AWS KMS.
# For now, we create a deterministic key for Fernet.
import base64
import hashlib

def get_fernet_key() -> bytes:
    """
    Returns the dedicated encryption key.
    Checks environment for specific key, raises error in production if missing.
    """
    key = settings.ENCRYPTION_KEY
    
    if not key:
        if settings.ENVIRONMENT == "production":
            raise ValueError("CRITICAL SECURITY ERROR: ENCRYPTION_KEY is missing in production!")
        # Fallback for dev ONLY (Deterministic hash of secret key)
        return base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    
    return key.encode()

# try:
#     fernet_client = Fernet(get_fernet_key())
# except Exception as e:
#     print(f"CRITICAL ERROR: Could not initialize Fernet encryption client. SECRET_KEY might be invalid. Error: {e}")
#     # In a real app, this should prevent startup.
#     fernet_client = None


def encrypt_data(data: str) -> str:
    """Encrypts a string using Fernet (Symmetric Encryption)."""
    if not data:
        return None
    f = Fernet(get_fernet_key())
    return f.encrypt(data.encode()).decode()



def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Decrypts a Fernet token."""
    if not encrypted_data:
        return None
    try:
        f = Fernet(get_fernet_key())
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return None








