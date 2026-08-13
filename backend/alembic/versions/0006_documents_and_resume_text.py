"""add documents table, resume_text, and application document links

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

document_type = postgresql.ENUM(
    "resume", "cover_letter", "portfolio", "certificate", "other",
    name="document_type", create_type=False,
)


def upgrade():
    bind = op.get_bind()
    document_type.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("resume_text", sa.Text(), nullable=True))

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", document_type, nullable=False, server_default="other"),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.add_column("applications", sa.Column("resume_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True))
    op.add_column("applications", sa.Column("cover_letter_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True))


def downgrade():
    op.drop_column("applications", "cover_letter_document_id")
    op.drop_column("applications", "resume_document_id")

    op.drop_table("documents")
    op.drop_column("users", "resume_text")

    bind = op.get_bind()
    document_type.drop(bind, checkfirst=True)
