from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from typing_extensions import Literal

class Settings(BaseSettings):
    """
    Pydantic settings model to load and validate all environment variables.
    """

    BACKEND_CORS_ORIGINS: Optional[List[Union[str, AnyHttpUrl]]] = None
    
    # --- Application Core ---
    ENVIRONMENT: Literal["development", "production"] = "development"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CRITICAL: Dedicated key for encrypting PII/Private Keys. 
    # Must be 32 url-safe base64-encoded bytes.
    ENCRYPTION_KEY: Optional[str] = None
    
    # --- Database (PostgreSQL) ---
    DATABASE_URL: PostgresDsn
    TEST_DATABASE_URL: Optional[PostgresDsn] = None

    # Scalability: Connection Pool Settings
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def db_url_validate(cls, v: Optional[str]) -> Optional[str]:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v
        
    @field_validator("TEST_DATABASE_URL", mode="before")
    @classmethod
    def test_db_url_validate(cls, v: Optional[str]) -> Optional[str]:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    # --- Cache & Task Broker (Redis) ---
    REDIS_URL: RedisDsn
    CELERY_BROKER_URL: RedisDsn
    CELERY_RESULT_BACKEND: RedisDsn

    # --- Blockchain RPC Endpoints ---
    BITCOIN_RPC_URL: AnyHttpUrl
    BITCOIN_SEPOLIA_RPC_URL: AnyHttpUrl
    SOLANA_RPC_URL: AnyHttpUrl
    SOLANA_DEVNET_RPC_URL: AnyHttpUrl
    BASE_RPC_URL: AnyHttpUrl
    BASE_SEPOLIA_RPC_URL: AnyHttpUrl
    POLYGON_RPC_URL: AnyHttpUrl
    POLYGON_MUMBAI_RPC_URL: AnyHttpUrl
    ETHEREUM_RPC_URL: AnyHttpUrl
    ETHEREUM_SEPOLIA_RPC_URL: AnyHttpUrl
    
    # --- Fiat On-Ramp (Stage 5) ---
    TRANSAK_API_KEY: Optional[str] = None
    TRANSAK_SECRET_KEY: Optional[str] = None
    RAMP_API_KEY: Optional[str] = None
    RAMP_SECRET_KEY: Optional[str] = None

    # --- Blockchain Analytics (Stage 10) ---
    CHAINALYSIS_API_KEY: Optional[str] = None
    
    # --- Market Data (Stage 14) ---
    COINGECKO_API_KEY: Optional[str] = None
    
    # --- Notifications (Stage 15) ---
    # Option 1: AWS SES
    AWS_SES_REGION: Optional[str] = None
    AWS_SES_ACCESS_KEY_ID: Optional[str] = None
    AWS_SES_SECRET_ACCESS_KEY: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    
    # Option 2: SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    
    # FCM (Firebase Cloud Messaging)
    FCM_SERVICE_ACCOUNT_KEY_PATH: Optional[str] = None

    # --- SMS (Stage 3) ---
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # --- KYC (Stage 3) ---
    SUMSUB_API_TOKEN: Optional[str] = None
    SUMSUB_SECRET_KEY: Optional[str] = None

    # --- AWS Configuration (S3, KMS) ---
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    KMS_KEY_ID: Optional[str] = None
    
    # --- Other ---
    SENTRY_DSN: Optional[AnyHttpUrl] = None
    
    # --- First Super Admin User (for init_db script) ---
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_USERNAME: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instantiate the settings object
settings = Settings()
