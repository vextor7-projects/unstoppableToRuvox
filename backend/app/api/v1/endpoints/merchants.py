from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user, get_current_merchant_user
from app.models.user import User
from app.models.merchant import MerchantTerminal
from app.schemas.merchant import (
    Merchant, 
    MerchantCreate, 
    MerchantUpdate,
    MerchantEmployee,
    MerchantEmployeeCreate,
    MerchantEmployeeUpdate,
    MerchantTerminal as MerchantTerminalSchema,
    MerchantTerminalCreate,
    MerchantTerminalUpdate,
    MerchantTerminalApiKeyResponse
)
from app.services.merchant_service import MerchantService
from app.utils.exceptions import BadRequestException, NotFoundException, ConflictException

router = APIRouter()

# --- Merchant Profile ---

@router.post("/register", response_model=Merchant, status_code=status.HTTP_201_CREATED)
async def register_merchant(
    merchant_in: MerchantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upgrade the current user account to a Merchant account.
    """
    service = MerchantService(db)
    try:
        return await service.register_merchant(current_user.id, merchant_in)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.detail)

@router.get("/me", response_model=Merchant)
async def get_merchant_me(
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get details of the current merchant profile.
    """
    service = MerchantService(db)
    return await service.get_merchant_profile(current_user.id)

@router.patch("/me", response_model=Merchant)
async def update_merchant_me(
    merchant_in: MerchantUpdate,
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update merchant profile details.
    """
    service = MerchantService(db)
    return await service.update_merchant_profile(current_user.id, merchant_in)


# --- Employee Management ---

@router.post("/employees", response_model=MerchantEmployee, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_in: MerchantEmployeeCreate,
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new employee account for this merchant.
    """
    service = MerchantService(db)
    try:
        return await service.add_employee(current_user.id, employee_in)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.detail)

@router.get("/employees", response_model=List[MerchantEmployee])
async def get_employees(
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all employees.
    """
    service = MerchantService(db)
    return await service.get_employees(current_user.id)

@router.patch("/employees/{employee_id}", response_model=MerchantEmployee)
async def update_employee(
    employee_id: uuid.UUID,
    employee_in: MerchantEmployeeUpdate,
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update an employee (e.g., deactivate or change role).
    """
    service = MerchantService(db)
    try:
        return await service.update_employee(current_user.id, employee_id, employee_in)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Employee not found.")

@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: uuid.UUID,
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete an employee.
    """
    service = MerchantService(db)
    try:
        await service.delete_employee(current_user.id, employee_id)
        return None
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Employee not found.")


# --- Terminal Management ---

@router.post("/terminals", response_model=MerchantTerminalApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_terminal(
    terminal_in: MerchantTerminalCreate,
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new POS terminal.
    Returns the API key ONLY ONCE.
    """
    service = MerchantService(db)
    terminal, api_key = await service.create_terminal(current_user.id, terminal_in)
    
    return MerchantTerminalApiKeyResponse(
        terminal_id=terminal.id,
        terminal_name=terminal.terminal_name,
        api_key=api_key
    )

@router.get("/terminals", response_model=List[MerchantTerminalSchema])
async def get_terminals(
    current_user: User = Depends(get_current_merchant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all active terminals.
    """
    service = MerchantService(db)
    return await service.get_terminals(current_user.id)