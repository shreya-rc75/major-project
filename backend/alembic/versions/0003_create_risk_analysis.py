"""Alembic migration: create risk_analysis table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_create_risk_analysis"
down_revision = "0002_create_stage_predictions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "risk_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_1y", sa.Float(), nullable=True),
        sa.Column("risk_3y", sa.Float(), nullable=True),
        sa.Column("risk_5y", sa.Float(), nullable=True),
        sa.Column("risk_category", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table("risk_analysis")
