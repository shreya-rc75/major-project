"""Alembic migration: create reports table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_create_reports"
down_revision = "0003_create_risk_analysis"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pdf_path", sa.String(length=1024), nullable=False),
        sa.Column("html_path", sa.String(length=1024), nullable=True),
        sa.Column("report_status", sa.String(length=32), nullable=False, server_default='created'),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table("reports")
