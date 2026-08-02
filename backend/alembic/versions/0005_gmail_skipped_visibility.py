"""add subject/sender to processed_gmail_messages for skipped-email visibility

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("processed_gmail_messages", sa.Column("subject", sa.String(500), nullable=True))
    op.add_column("processed_gmail_messages", sa.Column("sender", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("processed_gmail_messages", "sender")
    op.drop_column("processed_gmail_messages", "subject")
