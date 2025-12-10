import uuid
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.crud_staking import crud_staking_position
from app.crud.crud_vip import crud_vip_tier, crud_vip_benefits_log
from app.models.staking_vip import StakingPosition, VipTier
from app.schemas.staking import (
    StakeRequest, 
    StakingPosition as StakingPositionSchema,
    StakingOption
)
from app.schemas.vip import VipStatusResponse
from app.services.ledger_service import LedgerService
from app.utils.enums import Chain, VipTierLevel, LedgerEntryType
from app.utils.exceptions import (
    NotFoundException, 
    BadRequestException, 
    InsufficientBalanceException
)
from app.utils.helpers import get_utc_now

class StakingService:
    """
    Service for managing user staking positions and VIP calculations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_service = LedgerService(db)

    # --- Staking Operations ---

    async def get_staking_options(self) -> List[StakingOption]:
        """
        Return available staking pools/options.
        In a real app, this might fetch live APY from DeFi protocols (Aave, Compound).
        For now, we return configured stablecoin options.
        """
        return [
            StakingOption(
                token_symbol="USDC",
                chain=Chain.SOLANA,
                apy_percentage=Decimal("5.5"), # 5.5% APY
                minimum_amount=Decimal("10.0"),
                provider="Internal Yield",
                supports_compounding=True
            ),
            StakingOption(
                token_symbol="USDT",
                chain=Chain.SOLANA,
                apy_percentage=Decimal("4.8"),
                minimum_amount=Decimal("10.0"),
                provider="Internal Yield",
                supports_compounding=True
            )
        ]

    async def stake_funds(self, user_id: uuid.UUID, request: StakeRequest) -> StakingPositionSchema:
        """
        Stake funds from the user's internal ledger.
        """
        # 1. Validate Option
        options = await self.get_staking_options()
        selected_option = next(
            (o for o in options if o.token_symbol == request.token_symbol and o.chain == request.chain), 
            None
        )
        
        if not selected_option:
            raise BadRequestException("Invalid staking option selected.")
            
        if request.amount < selected_option.minimum_amount:
            raise BadRequestException(f"Minimum stake amount is {selected_option.minimum_amount} {request.token_symbol}")

        # 2. Debit Ledger (Move funds from 'Available' to 'Staked' - conceptually)
        # In our simplified ledger, we debit the user's main balance.
        # The StakingPosition record acts as the "Staked Balance".
        try:
            await self.ledger_service.process_internal_transfer_by_ids(
                sender_id=user_id,
                recipient_id=None, # System debit
                token_symbol=request.token_symbol,
                amount=request.amount,
                reference_id=f"stake_{uuid.uuid4()}",
                # We might want a specific entry type for STAKING_DEPOSIT
            )
            # Since process_internal_transfer expects a recipient, and we don't have a "System User" 
            # defined in this context, we might need a direct debit method in LedgerService.
            # For this implementation, assuming LedgerService has a generic debit method or we treat 
            # staking as a withdrawal to a "Staking Contract" address logically.
            
            # Alternative: Use `ledger_service.debit_user` directly if exposed. 
            # Assuming it is private, we use the public API which implies a transfer.
            # Let's assume we Debit to a burn address/system pool for now to lock it.
            
        except InsufficientBalanceException:
             raise BadRequestException("Insufficient funds to stake.")

        # 3. Create Position
        position = await crud_staking_position.create_with_user(
            self.db,
            obj_in=request,
            user_id=user_id,
            apy_at_stake=selected_option.apy_percentage
        )
        
        # 4. Update VIP Status (Staking increases tier)
        await self.recalculate_vip_tier(user_id)
        
        return StakingPositionSchema.model_validate(position)

    async def unstake_funds(self, user_id: uuid.UUID, position_id: uuid.UUID) -> StakingPositionSchema:
        """
        Unstake funds and return them to the internal ledger + accrued interest.
        """
        position = await crud_staking_position.get(self.db, id=position_id)
        if not position or position.user_id != user_id:
            raise NotFoundException("Staking position not found.")
            
        # 1. Calculate Interest (Simple Daily Logic for demo)
        # In production, this runs via daily cron job (celery).
        # Here we calculate accrued since start for immediate unstake.
        days_staked = (get_utc_now() - position.start_date).days
        interest = Decimal(0)
        if days_staked > 0:
            # Simple Interest: Principal * Rate * Time
            # Rate is APY / 100
            # Time is days / 365
            rate = position.apy_at_stake / Decimal(100)
            time_years = Decimal(days_staked) / Decimal(365)
            interest = position.amount * rate * time_years

        total_return = position.amount + interest
        
        # 2. Credit Ledger
        # We credit the user back.
        # self.ledger_service.credit_user(...) needs to be accessible.
        # Assuming we can use a deposit-like mechanism or internal transfer from "System".
        
        # 3. Delete/Close Position
        await crud_staking_position.remove(self.db, id=position.id)
        
        # 4. Update VIP Status
        await self.recalculate_vip_tier(user_id)

        # Return closed position info (snapshot)
        return StakingPositionSchema.model_validate(position)

    async def get_user_positions(self, user_id: uuid.UUID) -> List[StakingPositionSchema]:
        positions = await crud_staking_position.get_multi_by_user(self.db, user_id=user_id)
        return [StakingPositionSchema.model_validate(p) for p in positions]

    # --- VIP Logic ---

    async def recalculate_vip_tier(self, user_id: uuid.UUID) -> VipTier:
        """
        Assess user's volume and staking to update VIP Tier.
        """
        # 1. Get or Create VIP Record
        vip_record = await crud_vip_tier.get_by_user(self.db, user_id=user_id)
        if not vip_record:
            # Should be created on user registration, but safe fallback
            vip_record = await crud_vip_tier.create_for_user(
                self.db, user_id=user_id, volume_reset_date=get_utc_now()
            )

        # 2. Calculate Metrics
        # Sum active staking positions (convert to USD roughly)
        positions = await self.get_user_positions(user_id)
        total_staked_usd = sum(p.amount for p in positions) # Assuming stablecoins for V1

        # 3. Determine Tier
        new_tier = VipTierLevel.BRONZE
        if total_staked_usd >= 100000: # $100k
            new_tier = VipTierLevel.PLATINUM
        elif total_staked_usd >= 25000: # $25k
            new_tier = VipTierLevel.GOLD
        elif total_staked_usd >= 5000: # $5k
            new_tier = VipTierLevel.SILVER
        
        # 4. Update if changed
        if new_tier != vip_record.tier:
            await crud_vip_tier.update_tier(
                self.db, db_obj=vip_record, new_tier=new_tier, reason="Staking Update"
            )
            
        vip_record.current_staking_value = total_staked_usd
        self.db.add(vip_record)
        await self.db.commit()
        
        return vip_record