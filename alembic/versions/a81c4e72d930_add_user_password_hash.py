"""Add user password hashes.

Revision ID: a81c4e72d930
Revises: c5a1d9e7f2b4
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a81c4e72d930"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "c5a1d9e7f2b4"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:

    op.add_column(
        "user_profiles",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:

    with op.batch_alter_table(
        "user_profiles",
    ) as batch_op:

        batch_op.drop_column(
            "password_hash"
        )
