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
# PIN / Password Hashing (passlib)
# -----------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# -----------------------------------------------------------------------------
# JSON Web Tokens (JWT) (python-jose)
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
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# -----------------------------------------------------------------------------
# Time-based One-Time Password (TOTP) (pyotp)
# -----------------------------------------------------------------------------

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def generate_totp_provisioning_uri(secret: str, email: str, issuer: str = "Ruvox") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def generate_totp_backup_codes(num_codes: int = 10, num_digits: int = 8) -> List[str]:
    return [pyotp.random_base32(length=num_digits) for _ in range(num_codes)]

# -----------------------------------------------------------------------------
# Data Encryption (cryptography - Fernet)
# -----------------------------------------------------------------------------

def get_fernet_key() -> bytes:
    """
    Returns the dedicated encryption key from environment variables.
    Requires ENCRYPTION_KEY to be set in .env
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("CRITICAL: ENCRYPTION_KEY is missing via settings.")
    
    if isinstance(key, str):
        return key.encode()
    return key

def encrypt_data(data: str) -> Optional[str]:
    """Encrypts a string using Fernet (Symmetric Encryption)."""
    if not data:
        return None
    try:
        f = Fernet(get_fernet_key())
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Decrypts a Fernet token."""
    if not encrypted_data:
        return None
    try:
        f = Fernet(get_fernet_key())
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None