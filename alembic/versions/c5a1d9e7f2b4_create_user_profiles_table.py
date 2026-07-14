"""Create user profiles table.

Revision ID: c5a1d9e7f2b4
Revises: fe9a336df075
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5a1d9e7f2b4"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "fe9a336df075"

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

    op.create_table(
        "user_profiles",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "public_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
        sa.Column(
            "telegram_user_id",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "display_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Africa/Lagos",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint(
            "telegram_user_id"
        ),
    )

    op.create_index(
        op.f(
            "ix_user_profiles_id"
        ),
        "user_profiles",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_user_profiles_public_id"
        ),
        "user_profiles",
        ["public_id"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_user_profiles_email"
        ),
        "user_profiles",
        ["email"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_user_profiles_telegram_user_id"
        ),
        "user_profiles",
        ["telegram_user_id"],
        unique=True,
    )


def downgrade() -> None:

    op.drop_index(
        op.f(
            "ix_user_profiles_telegram_user_id"
        ),
        table_name="user_profiles",
    )

    op.drop_index(
        op.f(
            "ix_user_profiles_email"
        ),
        table_name="user_profiles",
    )

    op.drop_index(
        op.f(
            "ix_user_profiles_public_id"
        ),
        table_name="user_profiles",
    )

    op.drop_index(
        op.f(
            "ix_user_profiles_id"
        ),
        table_name="user_profiles",
    )

    op.drop_table(
        "user_profiles"
    )
