"""add phone number and avatar to users

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-26

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("phone_number", sa.String(30), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(500), nullable=True))


def downgrade():
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "phone_number")
