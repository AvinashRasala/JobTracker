"""add gmail sync tracking

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("last_gmail_sync_at", sa.DateTime(), nullable=True))

    op.create_table(
        "processed_gmail_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gmail_message_id", sa.String(255), nullable=False),
        sa.Column("action_taken", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),
    )
    op.create_index("ix_processed_gmail_messages_user_id", "processed_gmail_messages", ["user_id"])
    op.create_index("ix_processed_gmail_messages_gmail_message_id", "processed_gmail_messages", ["gmail_message_id"])


def downgrade():
    op.drop_table("processed_gmail_messages")
    op.drop_column("users", "last_gmail_sync_at")
