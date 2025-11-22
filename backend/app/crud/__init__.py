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
from .crud_ledger import crud_ledger
from .crud_payment import crud_payment
from .crud_invoice import crud_invoice
from .crud_subscription import crud_subscription
from .crud_merchant import crud_merchant
from .crud_staking import crud_staking
from .crud_vip import crud_vip
from .crud_compliance import crud_compliance
from .crud_market import crud_market

# Note: The 'base' module is not exported as it's a generic class
# intended for inheritance, not direct use.