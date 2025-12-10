import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.db.base_class import Base, SoftDeleteMixin

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD operations.
    PRODUCTION FIX: Uses db.flush() instead of db.commit() to support atomic transactions.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ModelType]:
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        
        # CRITICAL FIX: Flush only. Let Service layer commit.
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        # CRITICAL FIX: Flush only.
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> None:
        """
        Hard delete. Use remove_soft for compliance data.
        """
        stmt = delete(self.model).where(self.model.id == id)
        await db.execute(stmt)
        # CRITICAL FIX: Flush only.
        await db.flush()

    async def remove_soft(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[ModelType]:
        """
        Soft delete. Marks record as deleted but keeps data.
        Requires model to inherit from SoftDeleteMixin.
        """
        if not issubclass(self.model, SoftDeleteMixin):
            raise NotImplementedError("Model does not support soft delete")

        db_obj = await self.get(db, id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now(timezone.utc)
            db.add(db_obj)
            await db.flush()
            return db_obj
        return None