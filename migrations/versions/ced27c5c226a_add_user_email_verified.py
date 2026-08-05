"""add user email_verified

Revision ID: ced27c5c226a
Revises: 224b08e7591d
Create Date: 2026-07-10 21:47:53.495505

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ced27c5c226a"
down_revision: Union[str, Sequence[str], None] = "224b08e7591d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "delivery_partner",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "seller",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Remove the default after existing rows have been updated
    op.alter_column(
        "delivery_partner",
        "email_verified",
        server_default=None,
    )

    op.alter_column(
        "seller",
        "email_verified",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("seller", "email_verified")
    op.drop_column("delivery_partner", "email_verified")