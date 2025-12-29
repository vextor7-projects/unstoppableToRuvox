"""
CRUD Package Initializer

This file makes the 'crud' directory a Python package and exports all the
individual CRUD (Create, Read, Update, Delete) objects.

This allows for cleaner imports in the service layer. Instead of:
    from app.crud.crud_user import crud_user
    from app.crud.crud_wallet import crud_wallet

We can just do:
    from app.crud import crud_user, crud_wallet
"""

from .crud_user import crud_user
from .crud_kyc import crud_kyc
from .crud_wallet import crud_wallet
from .crud_ledger import (
    crud_ledger,
    crud_withdrawal_request,
    crud_deposit_transaction
)
from .crud_payment import (
    crud_payment_session,
    crud_payment_transaction,
    crud_swap_transaction,
    crud_fee_distribution
)
from .crud_invoice import crud_invoice
from .crud_subscription import crud_subscription
from .crud_merchant import crud_merchant
from .crud_staking import (
    crud_interest_accrual,
    crud_staking_position
)
from .crud_vip import (
    crud_vip_tier,
    crud_tier_history,
    crud_vip_benefits_log
)
from .crud_compliance import (
    crud_travel_rule,
    crud_blockchain_screening,
    crud_suspicious_activity,
    crud_compliance_report,
    crud_regulatory_submission
)
from .crud_market import (
    crud_price_alert,
    crud_price_snapshot,
)

# Note: The 'base' module is not exported as it's a generic class
# intended for inheritance, not direct use.