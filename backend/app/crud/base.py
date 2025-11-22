import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base_class import Base

# Define TypeVariables for generic class
# ModelType represents the SQLAlchemy model (e.g., User, Wallet)
ModelType = TypeVar("ModelType", bound=Base)
# CreateSchemaType represents the Pydantic schema for creation (e.g., UserCreate)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# UpdateSchemaType represents the Pydantic schema for updates (e.g., UserUpdate)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD (Create, Read, Update, Delete) operations.

    This class provides a standard set of methods to interact with a specific
    SQLAlchemy model.

    Parameters:
        - `model`: The SQLAlchemy model class.
        - `CreateSchemaType`: The Pydantic schema for creating an instance.
        - `UpdateSchemaType`: The Pydantic schema for updating an instance.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUD object with the SQLAlchemy model.

        :param model: A SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ModelType]:
        """
        Get a single object by its primary key (id).

        :param db: The asynchronous database session.
        :param id: The UUID primary key of the object to retrieve.
        :return: The database object if found, otherwise None.
        """
        # Use db.get for efficient primary key lookup
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple objects with optional pagination.

        :param db: The asynchronous database session.
        :param skip: Number of objects to skip (offset).
        :param limit: Maximum number of objects to return.
        :return: A list of database objects.
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new object in the database.

        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing the creation data.
        :return: The newly created database object.
        """
        # Convert Pydantic schema to a dictionary
        obj_in_data = obj_in.model_dump()
        
        # Create a new SQLAlchemy model instance
        db_obj = self.model(**obj_in_data)
        
        # Add the new object to the session
        db.add(db_obj)
        
        # Commit the transaction to save the object
        await db.commit()
        
        # Refresh the object to get database-generated values (like ID, created_at)
        await db.refresh(db_obj)
        
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing object in the database.

        :param db: The asynchronous database session.
        :param db_obj: The existing database object to update.
        :param obj_in: The Pydantic schema or dict containing the update data.
        :return: The updated database object.
        """
        # Get the update data from the schema or dict
        if isinstance(obj_in, BaseModel):
            # Use exclude_unset=True to only update fields that were explicitly set
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in
        
        # Iterate over the update data and set the new values on the db_obj
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Add the updated object to the session (it's already tracked,
        # but db.add() is safe and handles all cases)
        db.add(db_obj)
        
        # Commit the transaction to save the changes
        await db.commit()
        
        # Refresh the object to reflect the changes
        await db.refresh(db_obj)
        
        return db_obj

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[ModelType]:
        """
        Remove an object from the database by its primary key (id).

        :param db: The asynchronous database session.
        :param id: The UUID primary key of the object to delete.
        :return: The deleted database object if found, otherwise None.
        """
        # First, get the object
        obj = await self.get(db, id)
        
        if obj:
            # If found, delete it
            await db.delete(obj)
            
            # Commit the transaction to apply the deletion
            await db.commit()
            
            return obj
        
        # If not found, return None
        return None