"""
Importing every model here ensures they're registered on Base.metadata
before Alembic's `--autogenerate` inspects it, and before `create_all`
runs in tests.
"""

from app.models.marketplace import Marketplace  # noqa: F401
from app.models.listing import Listing  # noqa: F401
