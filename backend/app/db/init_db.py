import asyncio
import logging

from app.core.config import settings
from app.crud.crud_user import crud_user
from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate
from app.utils.enums import UserRole, KycStatus, UserStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db() -> None:
    """
    Initialize the database with the first superuser.
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Creating initial data...")
            
            user = await crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
            
            if not user:
                logger.info(f"Creating superuser: {settings.FIRST_SUPERUSER_EMAIL}")
                
                user_in = UserCreate(
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    username=settings.FIRST_SUPERUSER_USERNAME,
                    pin=settings.FIRST_SUPERUSER_PASSWORD, # In this app context, password serves as PIN
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                )
                
                # Create the user using standard CRUD (handles hashing and security table creation)
                user = await crud_user.create(db, obj_in=user_in)
                
                # Manually elevate to superuser and verify KYC
                # We do this directly because UserCreate schema typically doesn't allow setting these fields
                user.is_superuser = True
                user.kyc_level = KycStatus.APPROVED_LEVEL_3
                
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                logger.info("Superuser created successfully.")
            else:
                logger.info("Superuser already exists. Skipping creation.")
                
        except Exception as e:
            logger.error(f"An error occurred during DB initialization: {e}")
            raise

async def main() -> None:
    logger.info("Initializing database service...")
    await init_db()
    logger.info("Database initialization finished.")

if __name__ == "__main__":
    asyncio.run(main())