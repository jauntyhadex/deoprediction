"""Add fixture updated_at column.

Revision ID: fe9a336df075
Revises: 133a0cddab7e
Create Date: 2026-07-14 06:29:23.774188
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fe9a336df075"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "133a0cddab7e"

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
        "fixtures",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE fixtures
        SET updated_at = created_at
        """
    )

    with op.batch_alter_table(
        "fixtures",
    ) as batch_op:

        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )


def downgrade() -> None:

    with op.batch_alter_table(
        "fixtures",
    ) as batch_op:

        batch_op.drop_column(
            "updated_at"
        )
