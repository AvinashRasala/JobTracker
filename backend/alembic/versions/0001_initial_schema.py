"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

application_status = postgresql.ENUM(
    "applied", "application_viewed", "under_review", "assessment", "coding_test",
    "interview_round_1", "interview_round_2", "interview_round_3", "hr_interview",
    "offer_received", "rejected", "withdrawn", "joined",
    name="application_status", create_type=False,
)
work_type = postgresql.ENUM("remote", "hybrid", "onsite", "unknown", name="work_type", create_type=False)
employment_type = postgresql.ENUM(
    "full_time", "part_time", "contract", "internship", "freelance", "unknown",
    name="employment_type", create_type=False,
)
data_source = postgresql.ENUM("gmail_parser", "chrome_extension", "manual", name="data_source", create_type=False)


def upgrade():
    bind = op.get_bind()
    application_status.create(bind, checkfirst=True)
    work_type.create(bind, checkfirst=True)
    employment_type.create(bind, checkfirst=True)
    data_source.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("google_access_token_encrypted", sa.String(), nullable=True),
        sa.Column("google_refresh_token_encrypted", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "platforms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("email_domain_pattern", sa.String(255), nullable=True),
        sa.Column("url_pattern", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "recruiters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platforms.id"), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recruiters.id"), nullable=True),
        sa.Column("role_title", sa.String(255), nullable=False),
        sa.Column("job_url", sa.String(1000), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(10), nullable=True, server_default="INR"),
        sa.Column("work_type", work_type, nullable=False, server_default="unknown"),
        sa.Column("employment_type", employment_type, nullable=False, server_default="unknown"),
        sa.Column("status", application_status, nullable=False, server_default="applied"),
        sa.Column("external_application_id", sa.String(255), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("resume_used", sa.String(500), nullable=True),
        sa.Column("source", data_source, nullable=False, server_default="manual"),
        sa.Column("source_email_id", sa.String(255), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=False),
        sa.Column("last_status_change_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_applied_at", "applications", ["applied_at"])

    op.create_table(
        "status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", application_status, nullable=True),
        sa.Column("to_status", application_status, nullable=False),
        sa.Column("changed_by", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_status_history_application_id", "status_history", ["application_id"])

    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_notes_application_id", "notes", ["application_id"])


def downgrade():
    op.drop_table("notes")
    op.drop_table("status_history")
    op.drop_table("applications")
    op.drop_table("recruiters")
    op.drop_table("platforms")
    op.drop_table("companies")
    op.drop_table("users")

    bind = op.get_bind()
    data_source.drop(bind, checkfirst=True)
    employment_type.drop(bind, checkfirst=True)
    work_type.drop(bind, checkfirst=True)
    application_status.drop(bind, checkfirst=True)
