import uuid
import secrets
from typing import List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash, verify_password
from app.crud.crud_merchant import crud_merchant
from app.models.merchant import (
    Merchant, 
    MerchantEmployee, 
    MerchantTerminal
)
from app.models.user import User
from app.schemas.merchant import (
    MerchantCreate, 
    MerchantUpdate,
    MerchantEmployeeCreate,
    MerchantEmployeeUpdate,
    MerchantTerminalCreate,
    MerchantTerminalUpdate
)
from app.utils.enums import (
    UserRole, 
    MerchantEmployeeRole, 
    KycStatus,
    SettlementStatus
)
from app.utils.exceptions import (
    NotFoundException, 
    BadRequestException, 
    ConflictException,
    NotAuthorizedException
)
from app.utils.helpers import generate_secure_random_string

class MerchantService:
    """
    Service for managing Merchant operations:
    - Profile management
    - Employee accounts (Cashiers/Managers)
    - POS Terminals & API Keys
    - Settlement logic
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Merchant Profile ---

    async def register_merchant(self, user_id: uuid.UUID, merchant_in: MerchantCreate) -> Merchant:
        """
        Upgrade a User account to a Merchant account.
        """
        # 1. Check if already a merchant
        existing = await crud_merchant.get(self.db, id=user_id)
        if existing:
            raise ConflictException("User is already a registered merchant.")

        # 2. Create Merchant Profile
        merchant = await crud_merchant.create_with_user(
            self.db, obj_in=merchant_in, user_id=user_id
        )
        
        # 3. Update User Role
        # We need to fetch the user to update their role
        # Assuming logic exists or handled via trigger/event. 
        # Here we do it explicitly if User model is accessible or via separate service call.
        # For simplicity, we assume the User role update happens via separate admin approval 
        # or we do it here if self-service registration is allowed.
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        if user and user.role == UserRole.USER:
            user.role = UserRole.MERCHANT
            self.db.add(user)
            await self.db.commit()
            
        return merchant

    async def get_merchant_profile(self, merchant_id: uuid.UUID) -> Merchant:
        merchant = await crud_merchant.get(self.db, id=merchant_id)
        if not merchant:
            raise NotFoundException("Merchant profile not found.")
        return merchant

    async def update_merchant_profile(
        self, merchant_id: uuid.UUID, update_in: MerchantUpdate
    ) -> Merchant:
        merchant = await self.get_merchant_profile(merchant_id)
        return await crud_merchant.update(self.db, db_obj=merchant, obj_in=update_in)

    # --- Employee Management ---

    async def add_employee(
        self, merchant_id: uuid.UUID, employee_in: MerchantEmployeeCreate
    ) -> MerchantEmployee:
        """
        Add a new employee (Cashier/Manager) to the merchant account.
        """
        # Check if email already exists globally or just within merchant context?
        # Usually globally unique emails for login.
        # Ideally check User table too if employees are Users, but here they are separate entities.
        
        existing = await crud_merchant.get_employee_by_email(self.db, email=employee_in.email)
        if existing:
            raise ConflictException("An employee with this email already exists.")

        return await crud_merchant.create_employee(
            self.db, obj_in=employee_in, merchant_id=merchant_id
        )

    async def get_employees(self, merchant_id: uuid.UUID) -> List[MerchantEmployee]:
        return await crud_merchant.get_employees(self.db, merchant_id=merchant_id)

    async def update_employee(
        self, merchant_id: uuid.UUID, employee_id: uuid.UUID, update_in: MerchantEmployeeUpdate
    ) -> MerchantEmployee:
        employee = await crud_merchant.get_employee(self.db, id=employee_id)
        if not employee or employee.merchant_id != merchant_id:
            raise NotFoundException("Employee not found.")
            
        return await crud_merchant.update_employee(
            self.db, db_obj=employee, obj_in=update_in
        )

    async def delete_employee(self, merchant_id: uuid.UUID, employee_id: uuid.UUID) -> None:
        employee = await crud_merchant.get_employee(self.db, id=employee_id)
        if not employee or employee.merchant_id != merchant_id:
            raise NotFoundException("Employee not found.")
            
        await crud_merchant.delete_employee(self.db, id=employee_id)

    # --- Terminal / API Key Management ---

    async def create_terminal(
        self, merchant_id: uuid.UUID, terminal_in: MerchantTerminalCreate
    ) -> Tuple[MerchantTerminal, str]:
        """
        Create a new POS terminal and generate a secure API key.
        Returns (Terminal, PlainApiKey). The plain key is shown ONLY once.
        """
        return await crud_merchant.create_terminal(
            self.db, obj_in=terminal_in, merchant_id=merchant_id
        )

    async def get_terminals(self, merchant_id: uuid.UUID) -> List[MerchantTerminal]:
        return await crud_merchant.get_by_merchant_id(self.db, merchant_id=merchant_id)

    async def authenticate_terminal(self, api_key: str) -> Optional[MerchantTerminal]:
        """
        Verify a terminal API key for POS requests.
        Used by dependency injection.
        """
        # This requires a lookup strategy. Since keys are hashed, we can't lookup by key directly
        # unless we store a key_id/prefix.
        # If using simple API keys, we might need to iterate or change architecture to include ID in key.
        # Strategy: Key format "vex_terminal_<uuid>_<random>"
        # We parse UUID to find terminal, then verify hash of random part.
        
        try:
            parts = api_key.split('_')
            if len(parts) != 4 or parts[0] != "vex" or parts[1] != "term":
                return None
            
            terminal_id_str = parts[2]
            terminal_id = uuid.UUID(terminal_id_str)
            secret_part = parts[3]
            
            terminal = await crud_merchant.get_terminal(self.db, id=terminal_id)
            if not terminal or not terminal.is_active:
                return None
                
            # Verify the full key (or just the secret part depending on how we hashed it)
            # In crud_merchant.create_terminal, we hashed the *entire* string.
            if verify_password(api_key, terminal.hashed_api_key):
                return terminal
                
        except (ValueError, IndexError):
            pass
            
        return None