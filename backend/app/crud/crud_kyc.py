import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import BaseCRUD
from app.models.kyc import KycSubmission
from app.models.user import User
from app.schemas.kyc import KycSubmissionCreate, KycSubmissionUpdate
from app.utils.enums import KycStatus


class CRUDKyc(BaseCRUD[KycSubmission, KycSubmissionCreate, KycSubmissionUpdate]):
    """
    CRUD operations for KYC (Know Your Customer) submissions.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: KycSubmissionCreate,
        user_id: uuid.UUID,
        external_submission_id: Optional[str] = None
    ) -> KycSubmission:
        """
        Create a new KYC submission linked to a specific user.
        The status defaults to PENDING upon creation.
        
        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing the creation data (e.g., level).
        :param user_id: The UUID of the user making the submission.
        :param external_submission_id: Optional ID from the KYC provider.
        :return: The newly created KycSubmission object.
        """
        # Create the KycSubmission instance
        db_obj = KycSubmission(
            **obj_in.model_dump(),
            user_id=user_id,
            status=KycStatus.PENDING,  # Submissions start as pending review
            external_submission_id=external_submission_id
        )
        
        # Add, commit, and refresh
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> List[KycSubmission]:
        """
        Get all KYC submissions for a specific user, ordered by most recent first.
        
        :param db: The asynchronous database session.
        :param user_id: The UUID of the user.
        :return: A list of KycSubmission objects.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_latest_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> Optional[KycSubmission]:
        """
        Get the most recent KYC submission for a specific user.
        
        :param db: The asynchronous database session.
        :param user_id: The UUID of the user.
        :return: The latest KycSubmission object, or None if none exist.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(
        self, db: AsyncSession, *, external_submission_id: str
    ) -> Optional[KycSubmission]:
        """
        Get a KYC submission by its external provider ID.
        This is primarily used for handling webhooks.
        
        :param db: The asynchronous database session.
        :param external_submission_id: The unique ID from the external KYC provider.
        :return: The matching KycSubmission object, or None if not found.
        """
        stmt = select(self.model).filter(
            self.model.external_submission_id == external_submission_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Instantiate the CRUD object for use in the application
crud_kyc = CRUDKyc(KycSubmission)