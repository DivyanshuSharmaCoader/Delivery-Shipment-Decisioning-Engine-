"""add cancelled status

Revision ID: 224b08e7591d
Revises: edab7189839a
Create Date: 2026-07-05 04:29:03.355974

"""
from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '224b08e7591d'
down_revision: Union[str, Sequence[str], None] = 'edab7189839a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE shipmentstatus ADD VALUE IF NOT EXISTS 'cancelled';"
    )
    


def downgrade() -> None:
    """Downgrade schema."""
    pass
