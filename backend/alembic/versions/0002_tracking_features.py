"""add interview rounds, CTC/referral/follow-up tracking

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

interview_mode = postgresql.ENUM(
    "phone", "video", "onsite", "assessment", "other",
    name="interview_mode", create_type=False,
)
interview_outcome = postgresql.ENUM(
    "pending", "cleared", "rejected", "rescheduled", "no_show",
    name="interview_outcome", create_type=False,
)


def upgrade():
    bind = op.get_bind()
    interview_mode.create(bind, checkfirst=True)
    interview_outcome.create(bind, checkfirst=True)

    # --- users: profile fields for experienced professionals ---
    op.add_column("users", sa.Column("current_ctc", sa.Numeric(12, 2), nullable=True))
    op.add_column("users", sa.Column("current_notice_period_days", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("years_of_experience", sa.Numeric(4, 1), nullable=True))

    # --- applications: CTC, referral, follow-up ---
    op.add_column("applications", sa.Column("expected_ctc", sa.Numeric(12, 2), nullable=True))
    op.add_column("applications", sa.Column("offered_ctc", sa.Numeric(12, 2), nullable=True))
    op.add_column("applications", sa.Column("notice_period_days", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("referred_by_name", sa.String(255), nullable=True))
    op.add_column("applications", sa.Column("referred_by_email", sa.String(255), nullable=True))
    op.add_column("applications", sa.Column("referred_by_relationship", sa.String(100), nullable=True))
    op.add_column("applications", sa.Column("follow_up_at", sa.DateTime(), nullable=True))
    op.create_index("ix_applications_follow_up_at", "applications", ["follow_up_at"])

    # --- interview_rounds ---
    op.create_table(
        "interview_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_name", sa.String(255), nullable=False),
        sa.Column("mode", interview_mode, nullable=False, server_default="video"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("interviewer_name", sa.String(255), nullable=True),
        sa.Column("interviewer_designation", sa.String(255), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("outcome", interview_outcome, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_interview_rounds_application_id", "interview_rounds", ["application_id"])


def downgrade():
    op.drop_table("interview_rounds")

    op.drop_index("ix_applications_follow_up_at", table_name="applications")
    op.drop_column("applications", "follow_up_at")
    op.drop_column("applications", "referred_by_relationship")
    op.drop_column("applications", "referred_by_email")
    op.drop_column("applications", "referred_by_name")
    op.drop_column("applications", "notice_period_days")
    op.drop_column("applications", "offered_ctc")
    op.drop_column("applications", "expected_ctc")

    op.drop_column("users", "years_of_experience")
    op.drop_column("users", "current_notice_period_days")
    op.drop_column("users", "current_ctc")

    bind = op.get_bind()
    interview_outcome.drop(bind, checkfirst=True)
    interview_mode.drop(bind, checkfirst=True)
