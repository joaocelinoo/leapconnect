"""add telegram_users and telegram_link_tokens tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "telegram_users" not in inspector.get_table_names():
        op.create_table(
            "telegram_users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("chat_id", sa.String(64), nullable=False, unique=True),
            sa.Column("username", sa.String(256), nullable=True),
            sa.Column("first_name", sa.String(256), nullable=True),
            sa.Column("last_name", sa.String(256), nullable=True),
            sa.Column(
                "status", sa.String(16), nullable=False, default="pending"
            ),  # pending, approved, rejected
            sa.Column("linked_token", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
        )

    if "telegram_link_tokens" not in inspector.get_table_names():
        op.create_table(
            "telegram_link_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("token", sa.String(64), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, default=False),
        )


def downgrade() -> None:
    op.drop_table("telegram_link_tokens")
    op.drop_table("telegram_users")
